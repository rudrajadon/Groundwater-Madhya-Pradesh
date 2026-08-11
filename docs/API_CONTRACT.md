# API Contract — v1

Base URL: `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000`)

## GET /api/v1/wells
Returns all validated wells for the map view.
```json
[{"well_id":"ASIND-001-PZ","lat":22.44,"lon":75.72,"block":"Depalpur","aquifer_zone":"Massive","trend_label":"Watch"}]
```

## GET /api/v1/wells/{well_id}/history
```json
{"well_id":"ASIND-001-PZ","readings":[{"date":"2020-01-01","depth_bgl_m":12.3,"head_msl_m":517.7}]}
```

## GET /api/v1/forecast?lat={lat}&lon={lon}
Core endpoint. Resolves the point to an existing well (snap within 2km) or
dynamically extends the graph (see backend/app/services/graph.py).
```json
{
  "well_id": "ASIND-001-PZ",
  "matched_existing_well": true,
  "distance_to_nearest_well_km": 0.0,
  "aquifer_zone": "Massive",
  "forecast": [{"month_index":1,"head_msl_m":516.9,"lower_m":514.2,"upper_m":519.6}, ...],
  "trend_label": "Watch",
  "recommendation": "Moderate decline projected...",
  "model_version": "pgnn_v3_2025-08-06",
  "caveat": null
}
```
**Status: stubbed (HTTP 501) until a trained model artifact exists** — see
`backend/app/routers/forecast.py` and `ml/train.py`. Contract is final;
only the model-loading wire-up in `app/main.py`'s lifespan handler remains.

## GET /api/v1/zones/summary
```json
{"zones":[{"aquifer_zone":"Weathered","n_wells":26},{"aquifer_zone":"Massive","n_wells":19}]}
```

## TODO (not yet implemented, noted for Phase 3 follow-up)
- `GET /api/v1/forecast/well/{well_id}` — convenience wrapper so the well
  detail page doesn't need to know coordinates.
- Auth on any future write endpoints (admin/data-entry, Phase 5).
