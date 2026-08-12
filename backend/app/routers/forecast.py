"""
Forecast router — PGNN-LSTM backed.
GET /api/v1/forecast?lat=&lon=          (nearest well or dynamic extension)
GET /api/v1/forecast/well/{well_id}     (exact well)
"""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ForecastPoint, ForecastResponse
from ..services.recommendation import caveat_for_zone, classify_trend

router = APIRouter(prefix="/api/v1/forecast", tags=["forecast"])

SEQ_LEN = 24


# ── helpers ───────────────────────────────────────────────────────────────────

def _require_model(request: Request):
    model = getattr(request.app.state, "model", None)
    if model is None:
        raise HTTPException(
            503,
            "Model not loaded. Run 'python ml/train.py' first, then restart the backend.",
        )
    return model


def _nearest_well(lat: float, lon: float, wells: list[dict]) -> tuple[dict, float]:
    """Return (well_dict, distance_km) for the closest well."""
    best, best_d = None, float("inf")
    for w in wells:
        d = ((w["lat"] - lat) ** 2 + (w["lon"] - lon) ** 2) ** 0.5 * 111
        if d < best_d:
            best_d, best = d, w
    return best, round(best_d, 2)


def _fetch_readings(well_id: str, db: Session, n: int = SEQ_LEN) -> list[float]:
    """Return the last n head_msl readings for a well, chronological order.
    
    IMPORTANT: The model was trained on head_msl (hydraulic head above mean sea level),
    NOT depth_bgl (depth below ground level). Using depth_bgl would invert the trend!
    """
    rows = db.execute(text("""
        SELECT head_msl_m AS wl
        FROM readings
        WHERE well_id = :wid AND head_msl_m IS NOT NULL
        ORDER BY date DESC
        LIMIT :n
    """), {"wid": well_id, "n": n}).mappings().all()
    return [float(r["wl"]) for r in reversed(rows)]


def _build_forecast_response(
    well_id: str,
    matched: bool,
    dist_km: float,
    zone: str,
    result: dict,
    model_version: str = "pgnn_lstm_v1",
    extra_caveat: str | None = None,
) -> ForecastResponse:
    heads = result["forecast_head_msl"]
    stds  = result["uncertainty_std_m"]
    trend_label, recommendation = classify_trend(heads)
    caveat_parts = [c for c in [caveat_for_zone(zone), extra_caveat] if c]

    return ForecastResponse(
        well_id=well_id,
        matched_existing_well=matched,
        distance_to_nearest_well_km=dist_km,
        aquifer_zone=zone or "Unknown",
        forecast=[
            ForecastPoint(
                month_index=i + 1,
                head_msl_m=round(heads[i], 2),
                lower_m=round(heads[i] - 1.96 * stds[i], 2),
                upper_m=round(heads[i] + 1.96 * stds[i], 2),
            )
            for i in range(len(heads))
        ],
        trend_label=trend_label,
        recommendation=recommendation,
        model_version=model_version,
        caveat=" ".join(caveat_parts) if caveat_parts else None,
    )


def _statistical_fallback(
    well_id: str, matched: bool, dist_km: float, zone: str, db: Session
) -> ForecastResponse:
    """Simple linear-trend fallback when ML model can't serve this well."""
    from ..services.statistical_trend import compute_statistical_trend
    trend = compute_statistical_trend(well_id, db, months_lookback=12)
    rows = db.execute(text("""
        SELECT head_msl_m FROM readings
        WHERE well_id = :wid AND head_msl_m IS NOT NULL
        ORDER BY date DESC LIMIT 1
    """), {"wid": well_id}).mappings().all()

    if not rows:
        return ForecastResponse(
            well_id=well_id,
            matched_existing_well=matched,
            distance_to_nearest_well_km=dist_km,
            aquifer_zone=zone or "Unknown",
            forecast=[],
            trend_label="Unknown",
            recommendation="No readings available for this well.",
            model_version="no_data",
            caveat="No water level measurements found in the database.",
        )

    recent = float(rows[0]["head_msl_m"])
    monthly = trend["slope_m_per_year"] / 12.0
    heads   = [recent + (i + 1) * monthly for i in range(12)]
    stds    = [1.5] * 12
    trend_label, rec = classify_trend(heads)

    return ForecastResponse(
        well_id=well_id,
        matched_existing_well=matched,
        distance_to_nearest_well_km=dist_km,
        aquifer_zone=zone or "Unknown",
        forecast=[
            ForecastPoint(
                month_index=i + 1,
                head_msl_m=round(heads[i], 2),
                lower_m=round(heads[i] - 1.96 * stds[i], 2),
                upper_m=round(heads[i] + 1.96 * stds[i], 2),
            )
            for i in range(12)
        ],
        trend_label=trend_label,
        recommendation=rec,
        model_version="statistical_fallback",
        caveat=(
            f"Insufficient data for ML model ({trend['n_readings']} readings). "
            f"Trend computed via {trend['method']} analysis "
            f"({trend['confidence']} confidence)."
        ),
    )


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=ForecastResponse)
def get_forecast(
    request: Request,
    lat: float = Query(...),
    lon: float = Query(...),
    db: Session = Depends(get_db),
):
    model = _require_model(request)

    # 1. Find nearest well in DB
    rows = db.execute(text("""
        SELECT well_id,
               ST_Y(geom::geometry) AS lat,
               ST_X(geom::geometry) AS lon,
               block, aquifer_zone, geology_type
        FROM wells WHERE geom IS NOT NULL
    """)).mappings().all()
    if not rows:
        raise HTTPException(404, "No wells in database — has the ETL pipeline run?")

    wells = [dict(r) for r in rows]
    nearest, dist_km = _nearest_well(lat, lon, wells)
    well_id = nearest["well_id"]
    zone    = nearest.get("aquifer_zone") or nearest.get("geology_type") or "Unknown"
    matched = dist_km < 2.0

    # 2. Get recent readings
    readings = _fetch_readings(well_id, db, SEQ_LEN)
    if len(readings) < SEQ_LEN:
        return _statistical_fallback(well_id, matched, dist_km, zone, db)

    # 3. Scale with this well's MinMaxScaler
    scaler = model._scalers.get(well_id)
    if scaler is None:
        return _statistical_fallback(well_id, matched, dist_km, zone, db)

    scaled = scaler.transform(
        np.array(readings).reshape(-1, 1)
    ).flatten()

    # 4. Run PGNN-LSTM
    if well_id in model.well_list:
        result = model.predict_well(well_id, scaled, None, None, zone, scaler)
        extra  = None if matched else (
            f"Nearest well is {dist_km} km away — forecast uses that well's model."
        )
    else:
        # Well not in training graph — dynamic extension
        existing_coords = [(w["lon"], w["lat"]) for w in wells]
        existing_zones  = [w.get("aquifer_zone", "Unknown") for w in wells]
        existing_blocks = [w.get("block", "") for w in wells]
        result = model.predict_point(
            lat, lon, zone, nearest.get("block", ""),
            scaled, None, None, scaler,
            existing_coords, existing_zones, existing_blocks,
        )
        extra = (
            f"Well '{well_id}' was not in the training set. "
            "Forecast uses dynamic graph extension — treat as lower-confidence."
        )

    return _build_forecast_response(well_id, matched, dist_km, zone, result,
                                    extra_caveat=extra)


@router.get("/well/{well_id}", response_model=ForecastResponse)
def get_forecast_for_well(
    well_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    model = _require_model(request)

    row = db.execute(text("""
        SELECT well_id,
               ST_Y(geom::geometry) AS lat,
               ST_X(geom::geometry) AS lon,
               block, aquifer_zone, geology_type
        FROM wells WHERE well_id = :wid AND geom IS NOT NULL
    """), {"wid": well_id}).mappings().fetchone()

    if not row:
        raise HTTPException(404, f"Well '{well_id}' not found or has no coordinates.")

    zone = row.get("aquifer_zone") or row.get("geology_type") or "Unknown"

    readings = _fetch_readings(well_id, db, SEQ_LEN)
    if len(readings) < SEQ_LEN:
        return _statistical_fallback(well_id, True, 0.0, zone, db)

    scaler = model._scalers.get(well_id)
    if scaler is None:
        return _statistical_fallback(well_id, True, 0.0, zone, db)

    scaled = scaler.transform(np.array(readings).reshape(-1, 1)).flatten()

    if well_id in model.well_list:
        result = model.predict_well(well_id, scaled, None, None, zone, scaler)
    else:
        result = model.predict_point(
            float(row["lat"]), float(row["lon"]),
            zone, row.get("block", ""),
            scaled, None, None, scaler,
            [], [], [],
        )

    return _build_forecast_response(well_id, True, 0.0, zone, result)
