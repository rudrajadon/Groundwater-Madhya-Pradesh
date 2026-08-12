"""
MP Stress Map Router - District-level groundwater stress choropleth.
Aggregates well data to show risk zones across Madhya Pradesh districts.
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..db import get_db

router = APIRouter(prefix="/api/v1/stress-map", tags=["stress_map"])


class DistrictStress(BaseModel):
    """District stress level data"""
    district: str
    total_wells: int
    critical_count: int
    watch_count: int
    stable_count: int
    unknown_count: int
    critical_pct: float
    watch_pct: float
    stable_pct: float
    risk_level: str  # "Critical", "High", "Moderate", "Low"
    risk_color: str  # Hex color for map
    avg_lat: float
    avg_lon: float


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature for district"""
    type: str = "Feature"
    properties: Dict
    geometry: Optional[Dict] = None


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection for all districts"""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


def classify_risk_level(critical_pct: float, watch_pct: float) -> tuple[str, str]:
    """
    Classify district risk level based on well trends.
    
    Risk Levels:
    - Critical: >40% wells critical OR >70% critical+watch
    - High: 20-40% critical OR 50-70% critical+watch
    - Moderate: 10-20% critical OR 30-50% critical+watch
    - Low: <10% critical AND <30% critical+watch
    
    Args:
        critical_pct: Percentage of critical wells
        watch_pct: Percentage of watch wells
        
    Returns:
        Tuple of (risk_level, hex_color)
    """
    combined_pct = critical_pct + watch_pct
    
    if critical_pct > 40 or combined_pct > 70:
        return ("Critical", "#dc2626")  # Red
    elif critical_pct > 20 or combined_pct > 50:
        return ("High", "#f59e0b")  # Orange
    elif critical_pct > 10 or combined_pct > 30:
        return ("Moderate", "#fbbf24")  # Yellow
    else:
        return ("Low", "#22c55e")  # Green


@router.get("/districts", response_model=List[DistrictStress])
async def get_district_stress_levels(
    min_wells: int = Query(5, ge=1, description="Minimum wells required for district inclusion"),
    db: Session = Depends(get_db)
):
    """
    Get groundwater stress levels aggregated by district.
    
    Returns summary statistics and risk classification for each district:
    - Total wells count
    - Critical/Watch/Stable well counts and percentages
    - Risk level (Critical/High/Moderate/Low)
    - Color coding for choropleth visualization
    
    **Risk Classification:**
    - **Critical:** >40% wells critical OR >70% declining
    - **High:** 20-40% critical OR 50-70% declining
    - **Moderate:** 10-20% critical OR 30-50% declining
    - **Low:** <10% critical AND <30% declining
    
    **Query Parameters:**
    - `min_wells`: Minimum wells required (default: 5)
    
    **Example:**
    ```
    GET /api/v1/stress-map/districts?min_wells=5
    ```
    """
    query = text("""
        SELECT 
            district,
            COUNT(*) as total_wells,
            SUM(CASE WHEN trend_label = 'Critical' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN trend_label = 'Watch' THEN 1 ELSE 0 END) as watch_count,
            SUM(CASE WHEN trend_label = 'Stable' THEN 1 ELSE 0 END) as stable_count,
            SUM(CASE WHEN trend_label = 'Unknown' OR trend_label IS NULL THEN 1 ELSE 0 END) as unknown_count,
            AVG(ST_Y(geom::geometry)) as avg_lat,
            AVG(ST_X(geom::geometry)) as avg_lon
        FROM wells
        WHERE 
            geom IS NOT NULL 
            AND district IS NOT NULL 
            AND district != 'Unknown'
            AND district != ''
        GROUP BY district
        HAVING COUNT(*) >= :min_wells
        ORDER BY district
    """)
    
    results = db.execute(query, {"min_wells": min_wells}).mappings().all()
    
    districts = []
    for row in results:
        total = row['total_wells']
        critical_count = row['critical_count']
        watch_count = row['watch_count']
        stable_count = row['stable_count']
        unknown_count = row['unknown_count']
        
        # Calculate percentages
        critical_pct = (critical_count / total * 100) if total > 0 else 0
        watch_pct = (watch_count / total * 100) if total > 0 else 0
        stable_pct = (stable_count / total * 100) if total > 0 else 0
        
        # Classify risk
        risk_level, risk_color = classify_risk_level(critical_pct, watch_pct)
        
        districts.append(DistrictStress(
            district=row['district'],
            total_wells=total,
            critical_count=critical_count,
            watch_count=watch_count,
            stable_count=stable_count,
            unknown_count=unknown_count,
            critical_pct=round(critical_pct, 1),
            watch_pct=round(watch_pct, 1),
            stable_pct=round(stable_pct, 1),
            risk_level=risk_level,
            risk_color=risk_color,
            avg_lat=round(float(row['avg_lat']), 4),
            avg_lon=round(float(row['avg_lon']), 4)
        ))
    
    return districts


@router.get("/geojson")
async def get_district_stress_geojson(
    min_wells: int = Query(5, ge=1, description="Minimum wells required"),
    db: Session = Depends(get_db)
):
    """
    Get district stress levels as GeoJSON FeatureCollection.
    
    Returns district boundaries (approximated from well locations) with properties:
    - District name
    - Well counts and trends
    - Risk level and color
    - Statistics
    
    **Note:** This uses convex hull approximation from well locations.
    For accurate district boundaries, integrate with a district shapefile.
    
    **Query Parameters:**
    - `min_wells`: Minimum wells required (default: 5)
    
    **Example:**
    ```
    GET /api/v1/stress-map/geojson?min_wells=5
    ```
    
    **Response Format:** GeoJSON FeatureCollection
    """
    query = text("""
        SELECT 
            district,
            COUNT(*) as total_wells,
            SUM(CASE WHEN trend_label = 'Critical' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN trend_label = 'Watch' THEN 1 ELSE 0 END) as watch_count,
            SUM(CASE WHEN trend_label = 'Stable' THEN 1 ELSE 0 END) as stable_count,
            SUM(CASE WHEN trend_label = 'Unknown' OR trend_label IS NULL THEN 1 ELSE 0 END) as unknown_count,
            ST_AsGeoJSON(
                ST_Buffer(
                    ST_ConvexHull(ST_Collect(geom::geometry)),
                    0.1
                )
            ) as geometry
        FROM wells
        WHERE 
            geom IS NOT NULL 
            AND district IS NOT NULL 
            AND district != 'Unknown'
            AND district != ''
        GROUP BY district
        HAVING COUNT(*) >= :min_wells
        ORDER BY district
    """)
    
    results = db.execute(query, {"min_wells": min_wells}).mappings().all()
    
    features = []
    for row in results:
        total = row['total_wells']
        critical_count = row['critical_count']
        watch_count = row['watch_count']
        stable_count = row['stable_count']
        unknown_count = row['unknown_count']
        
        # Calculate percentages
        critical_pct = (critical_count / total * 100) if total > 0 else 0
        watch_pct = (watch_count / total * 100) if total > 0 else 0
        stable_pct = (stable_count / total * 100) if total > 0 else 0
        
        # Classify risk
        risk_level, risk_color = classify_risk_level(critical_pct, watch_pct)
        
        # Parse geometry
        import json
        geometry = json.loads(row['geometry']) if row['geometry'] else None
        
        features.append(GeoJSONFeature(
            type="Feature",
            properties={
                "district": row['district'],
                "total_wells": total,
                "critical_count": critical_count,
                "watch_count": watch_count,
                "stable_count": stable_count,
                "unknown_count": unknown_count,
                "critical_pct": round(critical_pct, 1),
                "watch_pct": round(watch_pct, 1),
                "stable_pct": round(stable_pct, 1),
                "risk_level": risk_level,
                "risk_color": risk_color,
            },
            geometry=geometry
        ))
    
    return GeoJSONFeatureCollection(
        type="FeatureCollection",
        features=features
    )


@router.get("/summary")
async def get_state_summary(db: Session = Depends(get_db)):
    """
    Get state-level summary statistics.
    
    Returns overall statistics for Madhya Pradesh:
    - Total districts
    - Total wells
    - Overall trend distribution
    - Districts by risk level
    
    **Example:**
    ```
    GET /api/v1/stress-map/summary
    ```
    """
    # Get overall statistics
    overall_query = text("""
        SELECT 
            COUNT(DISTINCT district) as total_districts,
            COUNT(*) as total_wells,
            SUM(CASE WHEN trend_label = 'Critical' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN trend_label = 'Watch' THEN 1 ELSE 0 END) as watch_count,
            SUM(CASE WHEN trend_label = 'Stable' THEN 1 ELSE 0 END) as stable_count,
            SUM(CASE WHEN trend_label = 'Unknown' OR trend_label IS NULL THEN 1 ELSE 0 END) as unknown_count
        FROM wells
        WHERE 
            geom IS NOT NULL 
            AND district IS NOT NULL 
            AND district != 'Unknown'
            AND district != ''
    """)
    
    overall = db.execute(overall_query).mappings().fetchone()
    
    if not overall:
        raise HTTPException(404, "No well data found")
    
    total_wells = overall['total_wells']
    
    # Calculate overall percentages
    critical_pct = (overall['critical_count'] / total_wells * 100) if total_wells > 0 else 0
    watch_pct = (overall['watch_count'] / total_wells * 100) if total_wells > 0 else 0
    stable_pct = (overall['stable_count'] / total_wells * 100) if total_wells > 0 else 0
    unknown_pct = (overall['unknown_count'] / total_wells * 100) if total_wells > 0 else 0
    
    # Get district risk distribution
    districts = await get_district_stress_levels(min_wells=5, db=db)
    
    risk_distribution = {
        "Critical": sum(1 for d in districts if d.risk_level == "Critical"),
        "High": sum(1 for d in districts if d.risk_level == "High"),
        "Moderate": sum(1 for d in districts if d.risk_level == "Moderate"),
        "Low": sum(1 for d in districts if d.risk_level == "Low"),
    }
    
    return {
        "state": "Madhya Pradesh",
        "total_districts": overall['total_districts'],
        "districts_with_data": len(districts),
        "total_wells": total_wells,
        "trend_distribution": {
            "critical": {
                "count": overall['critical_count'],
                "percentage": round(critical_pct, 1)
            },
            "watch": {
                "count": overall['watch_count'],
                "percentage": round(watch_pct, 1)
            },
            "stable": {
                "count": overall['stable_count'],
                "percentage": round(stable_pct, 1)
            },
            "unknown": {
                "count": overall['unknown_count'],
                "percentage": round(unknown_pct, 1)
            }
        },
        "risk_distribution": risk_distribution,
        "overall_risk_level": classify_risk_level(critical_pct, watch_pct)[0],
        "notes": "Risk levels based on Critical and Watch well percentages"
    }


@router.get("/district/{district_name}")
async def get_district_details(
    district_name: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific district.
    
    Returns:
    - District statistics
    - List of wells in district
    - Risk assessment
    - Recommendations
    
    **Path Parameters:**
    - `district_name`: District name (case-insensitive)
    
    **Example:**
    ```
    GET /api/v1/stress-map/district/Bhopal
    ```
    """
    # Get district statistics
    stats_query = text("""
        SELECT 
            COUNT(*) as total_wells,
            SUM(CASE WHEN trend_label = 'Critical' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN trend_label = 'Watch' THEN 1 ELSE 0 END) as watch_count,
            SUM(CASE WHEN trend_label = 'Stable' THEN 1 ELSE 0 END) as stable_count,
            SUM(CASE WHEN trend_label = 'Unknown' OR trend_label IS NULL THEN 1 ELSE 0 END) as unknown_count,
            AVG(ST_Y(geom::geometry)) as avg_lat,
            AVG(ST_X(geom::geometry)) as avg_lon
        FROM wells
        WHERE 
            geom IS NOT NULL 
            AND LOWER(district) = LOWER(:district)
    """)
    
    stats = db.execute(stats_query, {"district": district_name}).mappings().fetchone()
    
    if not stats or stats['total_wells'] == 0:
        raise HTTPException(404, f"District '{district_name}' not found or has no wells")
    
    total = stats['total_wells']
    critical_count = stats['critical_count']
    watch_count = stats['watch_count']
    stable_count = stats['stable_count']
    unknown_count = stats['unknown_count']
    
    # Calculate percentages
    critical_pct = (critical_count / total * 100) if total > 0 else 0
    watch_pct = (watch_count / total * 100) if total > 0 else 0
    stable_pct = (stable_count / total * 100) if total > 0 else 0
    
    # Classify risk
    risk_level, risk_color = classify_risk_level(critical_pct, watch_pct)
    
    # Get well list
    wells_query = text("""
        SELECT 
            well_id,
            block,
            ST_Y(geom::geometry) as lat,
            ST_X(geom::geometry) as lon,
            trend_label,
            geology_type,
            aquifer_classification
        FROM wells
        WHERE 
            geom IS NOT NULL 
            AND LOWER(district) = LOWER(:district)
        ORDER BY 
            CASE trend_label
                WHEN 'Critical' THEN 1
                WHEN 'Watch' THEN 2
                WHEN 'Stable' THEN 3
                ELSE 4
            END,
            well_id
        LIMIT 100
    """)
    
    wells = db.execute(wells_query, {"district": district_name}).mappings().all()
    
    # Generate recommendations
    recommendations = []
    if risk_level == "Critical":
        recommendations.append("URGENT: Implement immediate groundwater management measures")
        recommendations.append("Restrict new groundwater extraction permits")
        recommendations.append("Promote rainwater harvesting and aquifer recharge")
        recommendations.append("Monitor critical wells monthly")
    elif risk_level == "High":
        recommendations.append("Enhance monitoring frequency for declining wells")
        recommendations.append("Develop district-level water conservation plan")
        recommendations.append("Implement demand-side management measures")
    elif risk_level == "Moderate":
        recommendations.append("Maintain current monitoring schedule")
        recommendations.append("Plan preventive conservation measures")
        recommendations.append("Educate stakeholders on sustainable use")
    else:
        recommendations.append("Continue regular monitoring")
        recommendations.append("Maintain sustainable extraction practices")
    
    return {
        "district": district_name.title(),
        "center": {
            "lat": round(float(stats['avg_lat']), 4),
            "lon": round(float(stats['avg_lon']), 4)
        },
        "statistics": {
            "total_wells": total,
            "critical_count": critical_count,
            "watch_count": watch_count,
            "stable_count": stable_count,
            "unknown_count": unknown_count,
            "critical_pct": round(critical_pct, 1),
            "watch_pct": round(watch_pct, 1),
            "stable_pct": round(stable_pct, 1),
        },
        "risk_assessment": {
            "level": risk_level,
            "color": risk_color,
            "severity_score": round(critical_pct + (watch_pct * 0.5), 1)
        },
        "recommendations": recommendations,
        "wells": [dict(w) for w in wells[:50]],  # Limit to 50 wells in response
        "total_wells_in_response": len(wells)
    }
