from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import WellSummary

router = APIRouter(prefix="/api/v1/wells", tags=["wells"])


@router.get("", response_model=list[WellSummary])
def list_wells(db: Session = Depends(get_db)):
    """All wells for the map view. trend_label is now cached in the database
    and updated periodically by a background job. See docs/API_CONTRACT.md."""
    rows = db.execute(text("""
        SELECT well_id, ST_Y(geom::geometry) AS lat, ST_X(geom::geometry) AS lon,
               block, aquifer_zone, trend_label, geology_type, aquifer_classification
        FROM wells
        WHERE geom IS NOT NULL
    """)).mappings().all()
    return [
        WellSummary(well_id=r["well_id"], lat=r["lat"], lon=r["lon"],
                    block=r["block"], aquifer_zone=r["aquifer_zone"], 
                    trend_label=r["trend_label"],
                    geology_type=r["geology_type"],
                    aquifer_classification=r["aquifer_classification"])
        for r in rows
    ]


@router.get("/{well_id}/history")
def well_history(well_id: str, db: Session = Depends(get_db)):
    # Verify the well exists
    well_exists = db.execute(
        text("SELECT 1 FROM wells WHERE well_id = :wid"), {"wid": well_id}
    ).fetchone()
    if not well_exists:
        raise HTTPException(status_code=404, detail=f"Well '{well_id}' not found")
    rows = db.execute(text("""
        SELECT date, depth_bgl_m, head_msl_m
        FROM readings WHERE well_id = :wid ORDER BY date
    """), {"wid": well_id}).mappings().all()
    return {"well_id": well_id, "readings": [dict(r) for r in rows]}
