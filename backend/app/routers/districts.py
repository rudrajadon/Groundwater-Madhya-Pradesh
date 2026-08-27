"""
Districts API - provides district boundaries and district-level statistics
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from typing import Optional
import json
from pathlib import Path

from ..db import engine

router = APIRouter(prefix="/districts", tags=["districts"])

# Path to GeoJSON files
# Try multiple locations: frontend public dir, tmp dir (Docker), current dir
GEO_DIR_OPTIONS = [
    Path(__file__).parent.parent.parent.parent / "frontend" / "public" / "geo",
    Path("/tmp"),
    Path(".") / "geo"
]

# Find the first existing GeoJSON file
DISTRICTS_GEOJSON = None
DISTRICTS_FULL_GEOJSON = None

for geo_dir in GEO_DIR_OPTIONS:
    simplified = geo_dir / "mp_districts_simplified.geojson"
    full = geo_dir / "mp_districts.geojson"
    if simplified.exists():
        DISTRICTS_GEOJSON = simplified
        DISTRICTS_FULL_GEOJSON = full if full.exists() else simplified
        break


@router.get("/boundaries")
async def get_district_boundaries(
    simplified: bool = Query(True, description="Return simplified boundaries for faster rendering")
):
    """
    Get Madhya Pradesh district boundary polygons as GeoJSON.
    
    - **simplified**: If true, returns simplified boundaries (1.9MB). If false, returns full resolution (47MB).
    
    Returns GeoJSON FeatureCollection with district polygons.
    """
    geojson_path = DISTRICTS_GEOJSON if simplified else DISTRICTS_FULL_GEOJSON
    
    if not geojson_path or not geojson_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"District boundaries file not found. Checked: {[str(d) for d in GEO_DIR_OPTIONS]}"
        )
    
    # Return as JSON response with proper content type
    with open(geojson_path, 'r') as f:
        geojson_data = json.load(f)
    
    return JSONResponse(content=geojson_data)


@router.get("/list")
async def list_districts():
    """
    Get list of all districts with well counts.
    
    Returns list of districts sorted by name with count of wells in each district.
    """
    conn = engine.connect()
    
    result = conn.execute(text("""
        SELECT 
            district,
            COUNT(*) as well_count,
            COUNT(CASE WHEN trend_label = 'Critical' THEN 1 END) as critical_count,
            COUNT(CASE WHEN trend_label = 'Watch' THEN 1 END) as watch_count,
            COUNT(CASE WHEN trend_label = 'Stable' THEN 1 END) as stable_count,
            AVG(forecast_decline_m) as avg_decline_m
        FROM wells
        WHERE geom IS NOT NULL AND district IS NOT NULL
        GROUP BY district
        ORDER BY district
    """))
    
    districts = []
    for row in result.mappings():
        avg_decline = row["avg_decline_m"]
        districts.append({
            "district": row["district"],
            "well_count": row["well_count"],
            "critical_count": row["critical_count"],
            "watch_count": row["watch_count"],
            "stable_count": row["stable_count"],
            "avg_decline_m": float(avg_decline) if avg_decline is not None and not (isinstance(avg_decline, float) and (avg_decline != avg_decline or avg_decline == float('inf') or avg_decline == float('-inf'))) else None
        })
    
    conn.close()
    return districts


@router.get("/{district_name}/stats")
async def get_district_stats(district_name: str):
    """
    Get detailed statistics for a specific district.
    
    - **district_name**: Name of the district (case-insensitive)
    
    Returns comprehensive stats including well counts, trends, geology breakdown, etc.
    """
    conn = engine.connect()
    
    # Get overall stats
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_wells,
            COUNT(CASE WHEN trend_label = 'Critical' THEN 1 END) as critical_count,
            COUNT(CASE WHEN trend_label = 'Watch' THEN 1 END) as watch_count,
            COUNT(CASE WHEN trend_label = 'Stable' THEN 1 END) as stable_count,
            COUNT(CASE WHEN trend_label = 'Unknown' THEN 1 END) as unknown_count,
            AVG(forecast_decline_m) as avg_decline_m,
            MAX(forecast_decline_m) as max_decline_m,
            MIN(forecast_decline_m) as min_decline_m,
            AVG(elevation_m) as avg_elevation_m
        FROM wells
        WHERE UPPER(district) = UPPER(:district) AND geom IS NOT NULL
    """), {"district": district_name})
    
    stats_row = result.mappings().fetchone()
    
    if not stats_row or stats_row["total_wells"] == 0:
        raise HTTPException(status_code=404, detail=f"District '{district_name}' not found or has no wells")
    
    # Get geology breakdown
    geology_result = conn.execute(text("""
        SELECT 
            geology_type,
            COUNT(*) as count,
            AVG(forecast_decline_m) as avg_decline_m
        FROM wells
        WHERE UPPER(district) = UPPER(:district) AND geom IS NOT NULL
        GROUP BY geology_type
        ORDER BY count DESC
    """), {"district": district_name})
    
    geology_breakdown = [
        {
            "geology_type": row["geology_type"],
            "count": row["count"],
            "avg_decline_m": float(row["avg_decline_m"]) if row["avg_decline_m"] else None
        }
        for row in geology_result.mappings()
    ]
    
    # Get aquifer breakdown
    aquifer_result = conn.execute(text("""
        SELECT 
            aquifer_classification,
            COUNT(*) as count,
            AVG(forecast_decline_m) as avg_decline_m
        FROM wells
        WHERE UPPER(district) = UPPER(:district) AND geom IS NOT NULL
        GROUP BY aquifer_classification
        ORDER BY count DESC
    """), {"district": district_name})
    
    aquifer_breakdown = [
        {
            "aquifer_type": row["aquifer_classification"],
            "count": row["count"],
            "avg_decline_m": float(row["avg_decline_m"]) if row["avg_decline_m"] else None
        }
        for row in aquifer_result.mappings()
    ]
    
    # Get top critical wells
    critical_wells_result = conn.execute(text("""
        SELECT 
            well_id,
            trend_label,
            forecast_decline_m,
            block,
            geology_type
        FROM wells
        WHERE UPPER(district) = UPPER(:district) 
            AND trend_label IN ('Critical', 'Watch')
            AND geom IS NOT NULL
        ORDER BY forecast_decline_m DESC
        LIMIT 10
    """), {"district": district_name})
    
    critical_wells = [
        {
            "well_id": row["well_id"],
            "trend_label": row["trend_label"],
            "forecast_decline_m": float(row["forecast_decline_m"]) if row["forecast_decline_m"] else None,
            "block": row["block"],
            "geology_type": row["geology_type"]
        }
        for row in critical_wells_result.mappings()
    ]
    
    conn.close()
    
    # Calculate percentages
    total = stats_row["total_wells"]
    
    return {
        "district": district_name,
        "total_wells": total,
        "critical_count": stats_row["critical_count"],
        "critical_pct": (stats_row["critical_count"] / total * 100) if total > 0 else 0,
        "watch_count": stats_row["watch_count"],
        "watch_pct": (stats_row["watch_count"] / total * 100) if total > 0 else 0,
        "stable_count": stats_row["stable_count"],
        "stable_pct": (stats_row["stable_count"] / total * 100) if total > 0 else 0,
        "unknown_count": stats_row["unknown_count"],
        "avg_decline_m": float(stats_row["avg_decline_m"]) if stats_row["avg_decline_m"] else None,
        "max_decline_m": float(stats_row["max_decline_m"]) if stats_row["max_decline_m"] else None,
        "min_decline_m": float(stats_row["min_decline_m"]) if stats_row["min_decline_m"] else None,
        "avg_elevation_m": float(stats_row["avg_elevation_m"]) if stats_row["avg_elevation_m"] else None,
        "geology_breakdown": geology_breakdown,
        "aquifer_breakdown": aquifer_breakdown,
        "top_critical_wells": critical_wells
    }


@router.get("/{district_name}/wells")
async def get_district_wells(
    district_name: str,
    trend: Optional[str] = Query(None, description="Filter by trend: Critical, Watch, Stable")
):
    """
    Get all wells in a specific district.
    
    - **district_name**: Name of the district (case-insensitive)
    - **trend**: Optional filter by trend label
    
    Returns list of wells with coordinates and basic info.
    """
    conn = engine.connect()
    
    query = """
        SELECT 
            well_id,
            ST_Y(geom::geometry) as lat,
            ST_X(geom::geometry) as lon,
            trend_label,
            forecast_decline_m,
            block,
            geology_type,
            aquifer_classification
        FROM wells
        WHERE UPPER(district) = UPPER(:district) AND geom IS NOT NULL
    """
    
    params = {"district": district_name}
    
    if trend:
        query += " AND UPPER(trend_label) = UPPER(:trend)"
        params["trend"] = trend
    
    query += " ORDER BY well_id"
    
    result = conn.execute(text(query), params)
    
    wells = [
        {
            "well_id": row["well_id"],
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "trend_label": row["trend_label"],
            "forecast_decline_m": float(row["forecast_decline_m"]) if row["forecast_decline_m"] else None,
            "block": row["block"],
            "geology_type": row["geology_type"],
            "aquifer_classification": row["aquifer_classification"]
        }
        for row in result.mappings()
    ]
    
    conn.close()
    
    if not wells:
        raise HTTPException(status_code=404, detail=f"No wells found in district '{district_name}'")
    
    return wells
