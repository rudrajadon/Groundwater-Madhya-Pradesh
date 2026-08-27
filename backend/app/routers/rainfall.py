"""
Rainfall API Endpoints
======================
Provides access to rainfall data for wells and districts.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from ..db.session import get_db

router = APIRouter(prefix="/api/v1/rainfall", tags=["rainfall"])


class RainfallRecord(BaseModel):
    date: date
    rainfall_mm: float


class RainfallResponse(BaseModel):
    well_id: str
    data: List[RainfallRecord]
    stats: dict


class DistrictRainfallResponse(BaseModel):
    district: str
    wells_count: int
    monthly_avg: List[dict]


@router.get("/{well_id}", response_model=RainfallResponse)
def get_well_rainfall(well_id: str, db: Session = Depends(get_db)):
    """Get rainfall time series for a specific well."""
    
    # Query rainfall data
    query = f"""
        SELECT date, rainfall_mm
        FROM rainfall
        WHERE well_id = '{well_id}'
        ORDER BY date
    """
    
    result = db.execute(query).fetchall()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"No rainfall data for well {well_id}")
    
    data = [{"date": row[0], "rainfall_mm": row[1]} for row in result]
    
    # Compute stats
    rainfall_values = [r["rainfall_mm"] for r in data]
    stats = {
        "mean": sum(rainfall_values) / len(rainfall_values),
        "median": sorted(rainfall_values)[len(rainfall_values) // 2],
        "annual_avg": sum(rainfall_values) / (len(rainfall_values) / 12) if len(rainfall_values) >= 12 else sum(rainfall_values)
    }
    
    return {
        "well_id": well_id,
        "data": data,
        "stats": stats
    }


@router.get("/district/{district}", response_model=DistrictRainfallResponse)
def get_district_rainfall(district: str, db: Session = Depends(get_db)):
    """Get aggregated rainfall for a district."""
    
    # Query district rainfall
    query = f"""
        SELECT 
            EXTRACT(MONTH FROM r.date) as month,
            AVG(r.rainfall_mm) as avg_rainfall
        FROM rainfall r
        JOIN wells w ON r.well_id = w.well_id
        WHERE w.district = '{district}'
        GROUP BY EXTRACT(MONTH FROM r.date)
        ORDER BY month
    """
    
    result = db.execute(query).fetchall()
    
    if not result:
        raise HTTPException(status_code=404, detail=f"No data for district {district}")
    
    monthly_avg = [{"month": int(row[0]), "rainfall_mm": row[1]} for row in result]
    
    # Count wells
    count_query = f"SELECT COUNT(DISTINCT well_id) FROM wells WHERE district = '{district}'"
    wells_count = db.execute(count_query).fetchone()[0]
    
    return {
        "district": district,
        "wells_count": wells_count,
        "monthly_avg": monthly_avg
    }


@router.get("/correlation/{well_id}")
def get_correlation_metrics(well_id: str):
    """Get rainfall-groundwater correlation metrics."""
    # Placeholder - would load from correlation_results.csv
    return {
        "well_id": well_id,
        "correlation": 0.62,
        "optimal_lag_months": 2,
        "note": "Correlation analysis results - see data/correlation_results.csv"
    }
