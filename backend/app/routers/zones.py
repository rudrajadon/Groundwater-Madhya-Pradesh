from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db

router = APIRouter(prefix="/api/v1/zones", tags=["zones"])


@router.get("/summary")
def zones_summary(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT aquifer_zone, COUNT(*) AS n_wells
        FROM wells WHERE aquifer_zone IS NOT NULL
        GROUP BY aquifer_zone
    """)).mappings().all()
    return {"zones": [dict(r) for r in rows]}
