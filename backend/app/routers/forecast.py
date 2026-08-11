"""
Core forecast endpoint. Ties together: nearest-well resolution / dynamic
graph extension (services/graph.py), model inference (ml/inference.py),
and the recommendation heuristic (services/recommendation.py).

Falls back to statistical trend analysis for wells not in the trained model.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ForecastPoint, ForecastResponse
from ..services.graph import resolve_query_point, build_extended_edges
from ..services.recommendation import caveat_for_zone, classify_trend
from ..services.statistical_trend import compute_statistical_trend

router = APIRouter(prefix="/api/v1/forecast", tags=["forecast"])


def _load_all_wells(db: Session) -> list[dict]:
    rows = db.execute(text("""
        SELECT well_id, ST_Y(geom::geometry) AS lat, ST_X(geom::geometry) AS lon,
               block, aquifer_zone
        FROM wells WHERE geom IS NOT NULL
    """)).mappings().all()
    return [dict(r) for r in rows]


def _get_model(request: Request):
    model = getattr(request.app.state, "model", None)
    if model is None:
        raise HTTPException(
            503,
            "Model not loaded. Train the model first (python ml/train.py) "
            "and ensure MODEL_ARTIFACT_DIR points to the artifacts directory."
        )
    return model


@router.get("", response_model=ForecastResponse)
def get_forecast(
    request: Request,
    lat: float = Query(...), lon: float = Query(...),
    db: Session = Depends(get_db),
):
    model = _get_model(request)
    wells = _load_all_wells(db)
    if not wells:
        raise HTTPException(404, "No wells loaded — has the ETL pipeline run?")

    resolved = resolve_query_point(lat, lon, wells)
    well = resolved["well"]
    matched = resolved["matched_existing_well"]
    dist_km = resolved["distance_km"]
    zone = well.get("aquifer_zone") or "Other"  # Default to "Other" if null

    # Get the scaler for inverse-transforming predictions
    # FIX: Updated model uses global StandardScaler, not per-well scalers
    well_id = well["well_id"]
    if hasattr(model, 'global_scaler') and model.global_scaler is not None:
        scaler = model.global_scaler
    elif hasattr(model, 'scalers') and model.scalers:
        # Fallback for backward compatibility with old per-well scalers
        scaler = model.scalers.get(well_id)
        if scaler is None:
            scaler = next(iter(model.scalers.values()), None)
    else:
        scaler = None
    
    if scaler is None:
        raise HTTPException(503, "No fitted scaler available for inference")

    # Get recent readings for this well to build the input sequence
    readings = db.execute(text("""
        SELECT head_msl_m FROM readings
        WHERE well_id = :wid AND head_msl_m IS NOT NULL
        ORDER BY date DESC LIMIT :seq_len
    """), {"wid": well_id, "seq_len": 24}).mappings().all()

    if len(readings) < 24:
        # Insufficient data for ML model - try statistical fallback
        if len(readings) == 0:
            # No data at all - return a graceful "no data" response
            return ForecastResponse(
                well_id=well_id,
                matched_existing_well=matched,
                distance_to_nearest_well_km=dist_km,
                aquifer_zone=zone,
                forecast=[],
                trend_label="Unknown",
                recommendation="No historical data available for this well. Forecasting requires at least 12 months of water level measurements.",
                model_version="no_data",
                caveat="This well has no recorded water level measurements in the database.",
            )
        else:
            # Some data but not enough for ML - use simple statistical trend
            print(f"[INFO] Well {well_id} has only {len(readings)} readings, using statistical fallback")
            trend_result = compute_statistical_trend(well_id, db, months_lookback=min(12, len(readings)))
            
            recent_head = float(readings[0]["head_msl_m"])
            monthly_change = trend_result["slope_m_per_year"] / 12.0
            forecast_heads = [recent_head + (i+1) * monthly_change for i in range(12)]
            
            forecast_points = [
                ForecastPoint(
                    month_index=i + 1,
                    head_msl_m=round(forecast_heads[i], 2),
                    lower_m=round(forecast_heads[i] - 2.0, 2),
                    upper_m=round(forecast_heads[i] + 2.0, 2),
                )
                for i in range(len(forecast_heads))
            ]
            
            return ForecastResponse(
                well_id=well_id,
                matched_existing_well=matched,
                distance_to_nearest_well_km=dist_km,
                aquifer_zone=zone,
                forecast=forecast_points,
                trend_label=trend_result["trend_label"],
                recommendation=trend_result["recommendation"],
                model_version="statistical_limited_data",
                caveat=f"Only {len(readings)} readings available. Forecast has high uncertainty. Standard ML model requires 24+ readings.",
            )

    # Readings come newest-first, reverse to chronological order
    import numpy as np
    raw_series = np.array([float(r["head_msl_m"]) for r in reversed(readings)]).reshape(-1, 1)
    scaled_series = scaler.transform(raw_series).flatten()

    import torch
    # Use the model's cached graph data (built at startup from database)
    well_in_model = well_id in model.well_list if hasattr(model, 'well_list') else False
    
    if not well_in_model:
        # Well not in trained model - use statistical trend instead
        print(f"[INFO] Well {well_id} not in model, using statistical trend analysis")
        trend_result = compute_statistical_trend(well_id, db, months_lookback=12)
        
        # Generate simple forecast assuming linear trend
        recent_head = float(readings[0]["head_msl_m"])  # Most recent reading
        monthly_change = trend_result["slope_m_per_year"] / 12.0
        
        forecast_heads = [recent_head + (i+1) * monthly_change for i in range(12)]
        uncertainty = [1.0] * 12  # Fixed uncertainty for statistical method
        
        forecast_points = [
            ForecastPoint(
                month_index=i + 1,
                head_msl_m=round(forecast_heads[i], 2),
                lower_m=round(forecast_heads[i] - 1.96, 2),
                upper_m=round(forecast_heads[i] + 1.96, 2),
            )
            for i in range(len(forecast_heads))
        ]
        
        caveat = (
            f"This well was not included in the ML model training. "
            f"Trend computed using {trend_result['method']} analysis "
            f"({trend_result['confidence']} confidence, {trend_result['n_readings']} readings). "
        )
        if zone:
            caveat = f"{caveat_for_zone(zone)} {caveat}"
        
        return ForecastResponse(
            well_id=well_id,
            matched_existing_well=matched,
            distance_to_nearest_well_km=dist_km,
            aquifer_zone=zone,
            forecast=forecast_points,
            trend_label=trend_result["trend_label"],
            recommendation=trend_result["recommendation"],
            model_version="statistical_v1",
            caveat=caveat,
        )
    
    # Well is in model - use ML prediction
    if hasattr(model, '_node_feat') and model._node_feat is not None:
        node_feat = model._node_feat
        adj = model._adj
        # Update aquifer zone from cached prep data if available
        if hasattr(model, '_aq_info') and model._aq_info:
            zone = model._aq_info.get(well_id, {}).get("dominant", zone)
    else:
        # Fallback: identity adjacency (predictions will be poor)
        print(f"[WARNING] Using fallback graph structure - predictions may be inaccurate")
        node_feat = torch.zeros(len(model.well_list), 8)
        adj = torch.eye(len(model.well_list))

    if matched:
        result = model.predict_well(
            well_id, scaled_series, node_feat, adj, zone, scaler
        )
    else:
        # The model's adjacency matrix corresponds exactly to model.well_list.
        # We must align the coords/zones/blocks to that exact list and order.
        well_by_id = {w["well_id"]: w for w in wells}
        existing_coords = []
        existing_zones = []
        existing_blocks = []
        
        for wid in model.well_list:
            w = well_by_id.get(wid)
            if w:
                existing_coords.append((w["lon"], w["lat"]))
                existing_zones.append(w.get("aquifer_zone", "Other"))
                existing_blocks.append(w.get("block", ""))
            else:
                # If a model well is somehow missing from the DB, use dummy values
                # (This should be rare since the model was trained on the DB data)
                existing_coords.append((lon, lat)) 
                existing_zones.append("Other")
                existing_blocks.append("")
                
        result = model.predict_point(
            lat, lon, zone, well.get("block", ""),
            scaled_series, node_feat, adj, scaler,
            existing_coords, existing_zones, existing_blocks
        )

    forecast_heads = result["forecast_head_msl"]
    uncertainty = result["uncertainty_std_m"]
    trend_label, recommendation = classify_trend(forecast_heads)
    caveat = caveat_for_zone(zone)
    if not matched:
        extra_caveat = (
            f"No monitored well within 2km (nearest: {dist_km}km). "
            "This forecast uses dynamic graph extension — treat as lower-confidence."
        )
        caveat = f"{caveat} {extra_caveat}" if caveat else extra_caveat

    forecast_points = [
        ForecastPoint(
            month_index=i + 1,
            head_msl_m=round(forecast_heads[i], 2),
            lower_m=round(forecast_heads[i] - 1.96 * uncertainty[i], 2),
            upper_m=round(forecast_heads[i] + 1.96 * uncertainty[i], 2),
        )
        for i in range(len(forecast_heads))
    ]

    return ForecastResponse(
        well_id=result["well_id"],
        matched_existing_well=matched,
        distance_to_nearest_well_km=dist_km,
        aquifer_zone=zone,
        forecast=forecast_points,
        trend_label=trend_label,
        recommendation=recommendation,
        model_version=model.meta.get("version_id", "unknown"),
        caveat=caveat,
    )


@router.get("/well/{well_id}", response_model=ForecastResponse)
def get_forecast_by_well_id(
    well_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Convenience endpoint: forecast for a specific well_id.
    
    If well is in the trained model, uses ML predictions.
    If not, falls back to statistical trend analysis.
    """
    model = _get_model(request)
    
    # Check if well exists in database
    row = db.execute(text("""
        SELECT well_id, ST_Y(geom::geometry) AS lat, ST_X(geom::geometry) AS lon,
               aquifer_zone
        FROM wells WHERE well_id = :wid AND geom IS NOT NULL
    """), {"wid": well_id}).mappings().fetchone()
    
    if not row:
        raise HTTPException(404, f"Well '{well_id}' not found or has no coordinates")
    
    zone = row.get("aquifer_zone") or "Other"
    
    # Check if well is in the trained model
    well_in_model = well_id in model.well_list if hasattr(model, 'well_list') else False
    
    if not well_in_model:
        # Use statistical trend analysis
        print(f"[INFO] Well {well_id} not in model, using statistical trend analysis")
        
        # Check if well has any data
        readings_count = db.execute(text("""
            SELECT COUNT(*) as count FROM readings
            WHERE well_id = :wid AND head_msl_m IS NOT NULL
        """), {"wid": well_id}).mappings().fetchone()
        
        if readings_count['count'] == 0:
            # No data at all
            return ForecastResponse(
                well_id=well_id,
                matched_existing_well=True,
                distance_to_nearest_well_km=0.0,
                aquifer_zone=zone,
                forecast=[],
                trend_label="Unknown",
                recommendation="No historical data available for this well. Forecasting requires water level measurements.",
                model_version="no_data",
                caveat="This well has no recorded water level measurements in the database.",
            )
        
        trend_result = compute_statistical_trend(well_id, db, months_lookback=12)
        
        # Get recent readings for projection
        readings = db.execute(text("""
            SELECT head_msl_m FROM readings
            WHERE well_id = :wid AND head_msl_m IS NOT NULL
            ORDER BY date DESC LIMIT 1
        """), {"wid": well_id}).mappings().all()
        
        if len(readings) == 0:
            # Should not happen after count check, but safety net
            return ForecastResponse(
                well_id=well_id,
                matched_existing_well=True,
                distance_to_nearest_well_km=0.0,
                aquifer_zone=zone,
                forecast=[],
                trend_label="Unknown",
                recommendation="No recent data available for forecasting.",
                model_version="no_data",
                caveat="Unable to retrieve recent readings for this well.",
            )
        
        recent_head = float(readings[0]["head_msl_m"])
        monthly_change = trend_result["slope_m_per_year"] / 12.0
        
        forecast_heads = [recent_head + (i+1) * monthly_change for i in range(12)]
        uncertainty = [1.5] * 12  # Fixed uncertainty
        
        forecast_points = [
            ForecastPoint(
                month_index=i + 1,
                head_msl_m=round(forecast_heads[i], 2),
                lower_m=round(forecast_heads[i] - 1.96 * uncertainty[i], 2),
                upper_m=round(forecast_heads[i] + 1.96 * uncertainty[i], 2),
            )
            for i in range(len(forecast_heads))
        ]
        
        caveat = (
            f"Well not in ML model training set. "
            f"Trend computed using {trend_result['method']} analysis "
            f"({trend_result['confidence']} confidence, R²={trend_result['r_squared']:.2f})."
        )
        
        return ForecastResponse(
            well_id=well_id,
            matched_existing_well=True,
            distance_to_nearest_well_km=0.0,
            aquifer_zone=zone,
            forecast=forecast_points,
            trend_label=trend_result["trend_label"],
            recommendation=trend_result["recommendation"],
            model_version="statistical_v1",
            caveat=caveat,
        )
    
    # Well is in model - use ML prediction via lat/lon endpoint
    return get_forecast(request=request, lat=row["lat"], lon=row["lon"], db=db)
