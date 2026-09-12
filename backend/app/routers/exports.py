"""
Policy PDF/CSV Export Router
Generate official groundwater reports for CGWB and state boards.
"""
import io
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..db import get_db
from ..services.report_generator import (
    generate_well_forecast_pdf,
    generate_wells_forecast_csv,
    generate_district_summary_pdf
)

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


class ExportRequest(BaseModel):
    """Request model for generating exports"""
    well_ids: Optional[List[str]] = None  # Specific wells, or None for all
    district: Optional[str] = None  # Filter by district
    format: str = "pdf"  # "pdf" or "csv"
    include_charts: bool = True  # Include visualizations in PDF
    report_type: str = "well"  # "well" or "district_summary"


def _require_model(request: Request):
    """Ensure ML model is loaded."""
    model = getattr(request.app.state, "model", None)
    if model is None:
        raise HTTPException(
            503,
            "Model not loaded. Run 'python ml/train.py' first, then restart the backend.",
        )
    return model


def _get_well_metadata(well_id: str, db: Session) -> dict:
    """Fetch well metadata from database."""
    query = text("""
        SELECT 
            well_id,
            district,
            block,
            ST_Y(geom::geometry) AS lat,
            ST_X(geom::geometry) AS lon,
            geology_type,
            aquifer_classification,
            trend_label,
            forecast_decline_m
        FROM wells
        WHERE well_id = :well_id
    """)
    
    result = db.execute(query, {"well_id": well_id}).mappings().fetchone()
    
    if not result:
        raise HTTPException(404, f"Well {well_id} not found")
    
    return dict(result)


def _get_wells_by_district(district: str, db: Session) -> List[dict]:
    """Fetch all wells in a district."""
    query = text("""
        SELECT 
            well_id,
            district,
            block,
            ST_Y(geom::geometry) AS lat,
            ST_X(geom::geometry) AS lon,
            geology_type,
            aquifer_classification,
            trend_label,
            forecast_decline_m
        FROM wells
        WHERE district = :district
        AND geom IS NOT NULL
        ORDER BY well_id
    """)
    
    results = db.execute(query, {"district": district}).mappings().all()
    return [dict(r) for r in results]


def _get_all_wells(db: Session, limit: int = 1000) -> List[dict]:
    """Fetch all wells (up to limit)."""
    query = text("""
        SELECT 
            well_id,
            district,
            block,
            ST_Y(geom::geometry) AS lat,
            ST_X(geom::geometry) AS lon,
            geology_type,
            aquifer_classification,
            trend_label,
            forecast_decline_m
        FROM wells
        WHERE geom IS NOT NULL
        ORDER BY district, well_id
        LIMIT :limit
    """)
    
    results = db.execute(query, {"limit": limit}).mappings().all()
    return [dict(r) for r in results]


def _get_forecast_for_well(well_id: str, model, db: Session) -> tuple:
    """
    Get forecast for a single well using the forecast endpoint.
    Uses cached forecasts if available, falls back to model if provided.
    Returns (forecast_points, recommendation, model_version, caveat)
    """
    from ..routers.forecast import get_forecast_for_well as forecast_endpoint
    from fastapi import Request
    
    # Create a mock request with the model (can be None)
    class MockRequest:
        class State:
            def __init__(self, model):
                self.model = model
        def __init__(self, model):
            self.app = type('obj', (object,), {'state': self.State(model)})()
    
    mock_request = MockRequest(model)
    
    try:
        # Use the forecast endpoint to get predictions (uses cache first)
        forecast_response = forecast_endpoint(well_id, mock_request, db)
        
        # Extract data from response
        forecast_points = forecast_response.forecast
        recommendation = forecast_response.recommendation
        model_version = forecast_response.model_version
        caveat = forecast_response.caveat
        
        # Convert ForecastPoint objects to dicts
        forecast_dicts = [
            {
                "month_index": p.month_index,
                "head_msl_m": p.head_msl_m,
                "lower_m": p.lower_m,
                "upper_m": p.upper_m,
            }
            for p in forecast_points
        ]
        
        return forecast_dicts, recommendation, model_version, caveat
        
    except HTTPException as e:
        # Handle case where well has no cached forecast and model is not loaded
        if e.status_code == 503:
            print(f"[EXPORT] Well {well_id} has no cached forecast and model not available")
            return [], "Forecast unavailable (no cache, model not loaded)", "cache-only", "Pre-calculated forecast not available for this well"
        raise
    except Exception as e:
        print(f"[EXPORT] Error getting forecast for {well_id}: {e}")
        return [], f"Forecast unavailable: {str(e)}", "error", "Could not generate forecast"


@router.options("/generate")
async def generate_export_options():
    """Handle CORS preflight requests"""
    return {}


@router.post("/generate")
async def generate_export(
    request: Request,
    export_req: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate groundwater forecast export (PDF or CSV).
    
    **Request Body:**
    ```json
    {
        "well_ids": ["BPL002-OW", "BPL003-OW"],  // Optional: specific wells
        "district": "Bhopal",                     // Optional: filter by district
        "format": "pdf",                          // "pdf" or "csv"
        "include_charts": true,                   // Include visualizations (PDF only)
        "report_type": "well"                     // "well" or "district_summary"
    }
    ```
    
    **Returns:** PDF or CSV file as streaming response
    
    **Examples:**
    - Single well PDF: `{"well_ids": ["BPL002-OW"], "format": "pdf"}`
    - District CSV: `{"district": "Bhopal", "format": "csv"}`
    - All wells CSV: `{"format": "csv"}`
    """
    # Model is optional now - we use cached forecasts
    model = getattr(request.app.state, "model", None)
    if model is None:
        print("[EXPORT] WARNING: Model not loaded, will use cached forecasts only")
    
    # Determine which wells to export
    if export_req.well_ids:
        wells = [_get_well_metadata(wid, db) for wid in export_req.well_ids]
        print(f"[EXPORT] Using {len(wells)} wells from well_ids list")
    elif export_req.district:
        wells = _get_wells_by_district(export_req.district, db)
        print(f"[EXPORT] Using {len(wells)} wells from district: {export_req.district}")
        if not wells:
            raise HTTPException(404, f"No wells found in district: {export_req.district}")
    else:
        wells = _get_all_wells(db, limit=1000)
        print(f"[EXPORT] Using {len(wells)} wells from _get_all_wells (no district specified)")
        if not wells:
            raise HTTPException(404, "No wells found in database")
    
    if not wells:
        raise HTTPException(400, "No wells selected for export")
    
    print(f"[EXPORT] Total wells to process: {len(wells)}")
    print(f"[EXPORT] Request params: district={export_req.district}, format={export_req.format}, report_type={export_req.report_type}")
    
    # Generate export based on format and type
    # Auto-detect report type: if multiple wells selected, use district summary for PDF
    if export_req.format == "pdf" and export_req.report_type == "well" and len(wells) > 1:
        export_req.report_type = "district_summary"
    
    if export_req.format == "pdf":
        if export_req.report_type == "well" and len(wells) == 1:
            # Single well detailed report
            well = wells[0]
            forecast_points, recommendation, model_version, caveat = _get_forecast_for_well(
                well['well_id'], model, db
            )
            
            well_data = {
                **well,
                'recommendation': recommendation,
                'model_version': model_version,
                'caveat': caveat,
                'confidence': 'High' if len(forecast_points) == 12 else 'Low'
            }
            
            buffer = io.BytesIO()
            generate_well_forecast_pdf(well_data, forecast_points, buffer, export_req.include_charts)
            buffer.seek(0)
            
            filename = f"groundwater_forecast_{well['well_id']}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            return StreamingResponse(
                buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        elif export_req.report_type == "district_summary":
            # District summary report
            district_name = export_req.district or "Multiple Districts"
            
            # Calculate statistics
            total_wells = len(wells)
            critical_count = sum(1 for w in wells if w.get('trend_label') == 'Critical')
            watch_count = sum(1 for w in wells if w.get('trend_label') == 'Watch')
            stable_count = sum(1 for w in wells if w.get('trend_label') == 'Stable')
            
            # Calculate average decline from database values
            declines = [w.get('forecast_decline_m', 0) for w in wells if w.get('forecast_decline_m') is not None]
            avg_decline = sum(declines) / len(declines) if declines else 0.0
            
            statistics = {
                'total_wells': total_wells,
                'critical_count': critical_count,
                'critical_pct': (critical_count / total_wells * 100) if total_wells > 0 else 0,
                'watch_count': watch_count,
                'watch_pct': (watch_count / total_wells * 100) if total_wells > 0 else 0,
                'stable_count': stable_count,
                'stable_pct': (stable_count / total_wells * 100) if total_wells > 0 else 0,
                'avg_decline_m': avg_decline
            }
            
            # Use forecast_decline_m from database (already calculated correctly)
            for well in wells:
                well['forecast_change'] = well.get('forecast_decline_m', 0.0) or 0.0
            
            buffer = io.BytesIO()
            generate_district_summary_pdf(district_name, wells, statistics, buffer)
            buffer.seek(0)
            
            filename = f"groundwater_summary_{district_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            return StreamingResponse(
                buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        else:
            raise HTTPException(400, "PDF format only supports single well or district_summary report types")
    
    elif export_req.format == "csv":
        # CSV export for multiple wells
        forecasts_data = {}
        
        for well in wells:
            forecast_points, recommendation, model_version, caveat = _get_forecast_for_well(
                well['well_id'], model, db
            )
            forecasts_data[well['well_id']] = forecast_points
            well['recommendation'] = recommendation
            well['model_version'] = model_version
        
        buffer = io.StringIO()
        generate_wells_forecast_csv(wells, forecasts_data, buffer)
        buffer.seek(0)
        
        filename = f"groundwater_forecasts_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:
        raise HTTPException(400, f"Unsupported format: {export_req.format}")


@router.get("/wells")
async def get_exportable_wells(
    district: Optional[str] = Query(None, description="Filter by district"),
    db: Session = Depends(get_db)
):
    """
    Get list of wells available for export.
    
    **Query Parameters:**
    - `district`: Optional district filter
    
    **Returns:** List of wells with metadata
    """
    if district:
        wells = _get_wells_by_district(district, db)
    else:
        wells = _get_all_wells(db, limit=100)
    
    return {
        "count": len(wells),
        "wells": wells
    }


@router.get("/districts")
async def get_districts(db: Session = Depends(get_db)):
    """
    Get list of districts with well counts.
    
    **Returns:** List of districts with metadata
    """
    query = text("""
        SELECT 
            district,
            COUNT(*) as well_count,
            SUM(CASE WHEN trend_label = 'Critical' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN trend_label = 'Watch' THEN 1 ELSE 0 END) as watch_count,
            SUM(CASE WHEN trend_label = 'Stable' THEN 1 ELSE 0 END) as stable_count
        FROM wells
        WHERE geom IS NOT NULL AND district IS NOT NULL AND district != 'Unknown'
        GROUP BY district
        ORDER BY district
    """)
    
    results = db.execute(query).mappings().all()
    
    return {
        "count": len(results),
        "districts": [dict(r) for r in results]
    }
