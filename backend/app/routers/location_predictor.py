"""
Custom Location Predictor - Spatial interpolation for any lat/lon in Madhya Pradesh.
Uses k-nearest wells with IDW interpolation to generate forecasts.
"""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ForecastPoint, ForecastResponse
from ..services.spatial_interpolation import (
    get_k_nearest_wells,
    inverse_distance_weighting,
    interpolate_forecasts,
    get_geology_from_neighbors,
    get_district_from_location,
    validate_location_in_mp
)
from ..services.recommendation import classify_trend

router = APIRouter(prefix="/api/v1/location", tags=["location"])

SEQ_LEN = 24


def _require_model(request: Request):
    """Ensure ML model is loaded."""
    model = getattr(request.app.state, "model", None)
    if model is None:
        raise HTTPException(
            503,
            "Model not loaded. Run 'python ml/train.py' first, then restart the backend.",
        )
    return model


def _fetch_readings(well_id: str, db: Session, n: int = SEQ_LEN) -> list[float]:
    """Return the last n depth_bgl readings for a well, chronological order."""
    rows = db.execute(text("""
        SELECT depth_bgl_m AS wl
        FROM readings
        WHERE well_id = :wid AND depth_bgl_m IS NOT NULL
        ORDER BY date DESC
        LIMIT :n
    """), {"wid": well_id, "n": n}).mappings().all()
    return [float(r["wl"]) for r in reversed(rows)]


@router.post("/predict", response_model=ForecastResponse)
def predict_custom_location(
    request: Request,
    lat: float = Query(..., ge=21.0, le=26.9, description="Latitude (21.0-26.9°N)"),
    lon: float = Query(..., ge=74.0, le=82.8, description="Longitude (74.0-82.8°E)"),
    k_neighbors: int = Query(5, ge=3, le=10, description="Number of nearest wells for interpolation"),
    db: Session = Depends(get_db),
):
    """
    Generate 12-month groundwater forecast for any location in Madhya Pradesh.
    
    Uses spatial interpolation from k-nearest wells:
    1. Find k nearest wells using PostGIS ST_Distance
    2. Get forecast for each well from PGNN-LSTM model
    3. Apply Inverse Distance Weighting (IDW) interpolation
    4. Return weighted forecast with uncertainty bounds
    
    **Example:**
    ```
    POST /api/v1/location/predict?lat=23.5&lon=77.4&k_neighbors=5
    ```
    
    **Returns:** 12-month forecast with interpolated values and uncertainty.
    """
    # Don't load model yet - only if we need it for uncached wells
    model = None
    
    # 1. Validate location is in Madhya Pradesh
    if not validate_location_in_mp(lat, lon):
        raise HTTPException(
            400,
            f"Location ({lat}, {lon}) is outside Madhya Pradesh bounds. "
            "MP range: Lat 21.0-26.9°N, Lon 74.0-82.8°E"
        )
    
    # 2. Find k nearest wells
    nearest_wells = get_k_nearest_wells(lat, lon, db, k=k_neighbors, max_distance_km=50.0)
    
    if not nearest_wells:
        raise HTTPException(
            404,
            f"No wells found within 50km of location ({lat}, {lon}). "
            "Try a location closer to monitoring stations."
        )
    
    if len(nearest_wells) < 3:
        raise HTTPException(
            400,
            f"Only {len(nearest_wells)} wells found within 50km. "
            "Need at least 3 for reliable interpolation. Try a different location."
        )
    
    # 3. Calculate IDW weights
    weights = inverse_distance_weighting(lat, lon, nearest_wells, power=2.0)
    
    # 4. Get forecasts for each nearest well (from cache or model)
    well_forecasts = {}
    
    for well in nearest_wells:
        well_id = well['well_id']
        
        # First, check if this well has a cached forecast
        cached_result = db.execute(text("""
            SELECT forecast_cache
            FROM wells
            WHERE well_id = :well_id AND forecast_cache IS NOT NULL
        """), {"well_id": well_id}).fetchone()
        
        if cached_result and cached_result[0]:
            # Use cached forecast
            cache = cached_result[0]
            forecast_points = cache.get('forecast', [])
            if forecast_points:
                well_forecasts[well_id] = [pt['head_msl_m'] for pt in forecast_points]
                continue
        
        # No cache available - ML model is disabled on production
        # Skip this well or raise error if we don't have enough cached wells
        print(f"[location_predictor] WARNING: Well {well_id} has no cached forecast")
        continue
    
    if not well_forecasts:
        raise HTTPException(
            500,
            f"Could not generate forecasts for any of the {len(nearest_wells)} nearest wells. "
            "Insufficient training data for this region."
        )
    
    # 5. Interpolate forecasts using IDW
    interpolated_forecast, uncertainty = interpolate_forecasts(
        nearest_wells, well_forecasts, weights, months=12
    )
    
    # 6. Determine geology and district
    geology = get_geology_from_neighbors(nearest_wells)
    district = get_district_from_location(lat, lon, db) or "Unknown"
    
    # 7. Classify trend
    trend_label, recommendation = classify_trend(interpolated_forecast)
    
    # 8. Build response
    avg_distance = round(np.mean([w['distance_km'] for w in nearest_wells]), 2)
    
    return ForecastResponse(
        well_id=f"CUSTOM_{lat:.4f}_{lon:.4f}",
        matched_existing_well=False,
        distance_to_nearest_well_km=round(nearest_wells[0]['distance_km'], 2),
        aquifer_zone=geology,
        forecast=[
            ForecastPoint(
                month_index=i + 1,
                head_msl_m=round(interpolated_forecast[i], 2),
                lower_m=round(interpolated_forecast[i] - 1.96 * uncertainty[i], 2),
                upper_m=round(interpolated_forecast[i] + 1.96 * uncertainty[i], 2),
            )
            for i in range(12)
        ],
        trend_label=trend_label,
        recommendation=recommendation,
        model_version=f"pgnn_lstm_idw_k{len(well_forecasts)}",
        caveat=(
            f"Interpolated forecast from {len(well_forecasts)} wells "
            f"(avg distance: {avg_distance} km). "
            f"Location: {district} district, {geology} geology. "
            f"Confidence decreases with distance from monitoring stations."
        )
    )


@router.get("/nearest-wells")
def get_nearest_wells_info(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    k: int = Query(5, ge=1, le=20, description="Number of wells to return"),
    db: Session = Depends(get_db),
):
    """
    Get information about k nearest monitoring wells to a location.
    
    Useful for understanding which wells influence a custom location forecast.
    
    **Example:**
    ```
    GET /api/v1/location/nearest-wells?lat=23.5&lon=77.4&k=5
    ```
    """
    if not validate_location_in_mp(lat, lon):
        raise HTTPException(
            400,
            f"Location ({lat}, {lon}) is outside Madhya Pradesh bounds."
        )
    
    nearest_wells = get_k_nearest_wells(lat, lon, db, k=k, max_distance_km=100.0)
    
    if not nearest_wells:
        raise HTTPException(
            404,
            f"No wells found within 100km of location ({lat}, {lon})."
        )
    
    # Calculate weights for visualization
    weights = inverse_distance_weighting(lat, lon, nearest_wells, power=2.0)
    
    # Add weights to well info
    for well in nearest_wells:
        well['interpolation_weight'] = round(weights.get(well['well_id'], 0.0), 4)
    
    return {
        "target_location": {"lat": lat, "lon": lon},
        "nearest_wells": nearest_wells,
        "count": len(nearest_wells),
        "avg_distance_km": round(np.mean([w['distance_km'] for w in nearest_wells]), 2),
        "max_distance_km": round(max([w['distance_km'] for w in nearest_wells]), 2),
    }
