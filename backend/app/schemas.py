from pydantic import BaseModel


class WellSummary(BaseModel):
    well_id: str
    lat: float
    lon: float
    block: str | None = None
    aquifer_zone: str | None = None
    trend_label: str | None = None   # 'Stable' | 'Watch' | 'Critical'


class ForecastPoint(BaseModel):
    month_index: int
    head_msl_m: float
    lower_m: float
    upper_m: float


class ForecastResponse(BaseModel):
    well_id: str
    matched_existing_well: bool
    distance_to_nearest_well_km: float | None = None
    aquifer_zone: str
    forecast: list[ForecastPoint]
    trend_label: str
    recommendation: str
    model_version: str
    caveat: str | None = None   # populated for Fractured zone / low-confidence cases
