"""
Spatial interpolation service for custom location predictions.
Uses k-nearest wells with Inverse Distance Weighting (IDW) or kriging.
"""
import numpy as np
from typing import List, Tuple, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


def get_k_nearest_wells(
    lat: float,
    lon: float,
    db: Session,
    k: int = 5,
    max_distance_km: float = 50.0
) -> List[Dict]:
    """
    Get k nearest wells using PostGIS ST_Distance.
    
    Args:
        lat: Target latitude
        lon: Target longitude
        db: Database session
        k: Number of nearest neighbors (default 5)
        max_distance_km: Maximum search radius in km (default 50km)
        
    Returns:
        List of well dicts with distance, sorted by proximity
    """
    query = text("""
        SELECT 
            well_id,
            ST_Y(geom::geometry) AS lat,
            ST_X(geom::geometry) AS lon,
            geology_type,
            aquifer_classification,
            trend_label,
            block,
            district,
            ST_Distance(
                geom,
                ST_SetSRID(ST_MakePoint(:target_lon, :target_lat), 4326)::geography
            ) / 1000.0 AS distance_km
        FROM wells
        WHERE geom IS NOT NULL
          AND ST_Distance(
              geom,
              ST_SetSRID(ST_MakePoint(:target_lon, :target_lat), 4326)::geography
          ) <= (:max_dist * 1000.0)
        ORDER BY ST_Distance(
            geom,
            ST_SetSRID(ST_MakePoint(:target_lon, :target_lat), 4326)::geography
        )
        LIMIT :k
    """)
    
    rows = db.execute(query, {
        "target_lat": lat,
        "target_lon": lon,
        "max_dist": max_distance_km,
        "k": k
    }).mappings().all()
    
    return [dict(r) for r in rows]


def inverse_distance_weighting(
    target_lat: float,
    target_lon: float,
    wells: List[Dict],
    power: float = 2.0
) -> Dict[str, float]:
    """
    Calculate IDW weights for interpolation.
    
    Formula: weight_i = 1 / (distance_i ^ power)
    Normalized so sum(weights) = 1
    
    Args:
        target_lat: Target latitude
        target_lon: Target longitude
        wells: List of well dicts with 'distance_km'
        power: IDW power parameter (default 2.0 = inverse square)
        
    Returns:
        Dict mapping well_id to normalized weight
    """
    if not wells:
        return {}
    
    # If target is very close to a well (<100m), use only that well
    if wells[0]['distance_km'] < 0.1:
        return {wells[0]['well_id']: 1.0}
    
    # Calculate inverse distance weights
    weights = {}
    total_weight = 0.0
    
    for well in wells:
        distance = well['distance_km']
        # Add small epsilon to avoid division by zero
        weight = 1.0 / (distance ** power + 1e-6)
        weights[well['well_id']] = weight
        total_weight += weight
    
    # Normalize weights
    if total_weight > 0:
        weights = {wid: w / total_weight for wid, w in weights.items()}
    
    return weights


def interpolate_forecasts(
    wells: List[Dict],
    well_forecasts: Dict[str, List[float]],
    weights: Dict[str, float],
    months: int = 12
) -> Tuple[List[float], List[float]]:
    """
    Interpolate forecasts using weighted average of k-nearest wells.
    
    Args:
        wells: List of well dicts
        well_forecasts: Dict mapping well_id to forecast array (head_msl_m values)
        weights: Dict mapping well_id to interpolation weight
        months: Number of months to forecast (default 12)
        
    Returns:
        Tuple of (interpolated_forecast, uncertainty_std)
    """
    if not wells or not well_forecasts:
        return [], []
    
    # Initialize arrays
    forecast = np.zeros(months)
    uncertainty = np.zeros(months)
    
    # Weighted average of forecasts
    for well_id, weight in weights.items():
        if well_id in well_forecasts and len(well_forecasts[well_id]) >= months:
            well_values = np.array(well_forecasts[well_id][:months])
            forecast += weight * well_values
    
    # Uncertainty estimation: higher when wells disagree or are far
    for well_id, weight in weights.items():
        if well_id in well_forecasts and len(well_forecasts[well_id]) >= months:
            well_values = np.array(well_forecasts[well_id][:months])
            # Variance from weighted mean
            variance = weight * (well_values - forecast) ** 2
            uncertainty += variance
    
    # Add distance-based uncertainty (farther = less certain)
    avg_distance = np.mean([w['distance_km'] for w in wells])
    distance_factor = 1.0 + (avg_distance / 10.0)  # +10% per 10km
    uncertainty = np.sqrt(uncertainty) * distance_factor
    
    # Minimum uncertainty bound
    uncertainty = np.maximum(uncertainty, 0.5)
    
    return forecast.tolist(), uncertainty.tolist()


def get_geology_from_neighbors(wells: List[Dict]) -> str:
    """
    Determine most common geology type from nearest wells.
    
    Args:
        wells: List of well dicts with 'geology_type'
        
    Returns:
        Most common geology type, or 'Mixed' if tied
    """
    if not wells:
        return "Unknown"
    
    from collections import Counter
    geologies = [w.get('geology_type', 'Unknown') for w in wells if w.get('geology_type')]
    
    if not geologies:
        return "Unknown"
    
    counts = Counter(geologies)
    most_common = counts.most_common(2)
    
    # If tied between multiple types, return "Mixed"
    if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
        return "Mixed"
    
    return most_common[0][0]


def get_district_from_location(lat: float, lon: float, db: Session) -> Optional[str]:
    """
    Get district name from lat/lon by finding nearest well's district.
    
    Args:
        lat: Latitude
        lon: Longitude
        db: Database session
        
    Returns:
        District name or None
    """
    query = text("""
        SELECT district
        FROM wells
        WHERE geom IS NOT NULL
        ORDER BY ST_Distance(
            geom,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
        )
        LIMIT 1
    """)
    
    result = db.execute(query, {"lat": lat, "lon": lon}).mappings().fetchone()
    return result['district'] if result else None


def validate_location_in_mp(lat: float, lon: float) -> bool:
    """
    Validate that coordinates are within Madhya Pradesh bounds.
    
    MP approximate bounds:
    - Latitude: 21.0°N to 26.9°N
    - Longitude: 74.0°E to 82.8°E
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        True if within MP bounds, False otherwise
    """
    MP_LAT_MIN, MP_LAT_MAX = 21.0, 26.9
    MP_LON_MIN, MP_LON_MAX = 74.0, 82.8
    
    return (MP_LAT_MIN <= lat <= MP_LAT_MAX and 
            MP_LON_MIN <= lon <= MP_LON_MAX)
