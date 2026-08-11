# Indore Groundwater Forecasting App — Master Project Plan

**Status:** Planning locked. Ready for build.
**Owner decision basis:** Derived directly from `IndorePZ.mdb` (actual schema/records inspected) and `PGNN_LSTM_Final_ReviewerCorrected.ipynb` (actual code + printed run outputs inspected) — not assumptions.
**Scope decided:** Web app first (CLART-inspired), API designed mobile-ready from day one, native/PWA mobile app as an explicit later phase.

---

## 0. Ground truth — what we are actually starting from

These facts are locked in from direct inspection and should not be re-litigated without a reason; they drive every decision below.

- **Data:** `IndorePZ.mdb` is a CGWB-style relational groundwater DB. Real, usable tables: well master (53 piezometers, `ASIND-0xx-PZ` IDs, lat/long as DMS strings, elevation, geology, block/tahsil, DWLR info), water-level readings (`PW-SWL`, `OW1/2/3-SWL`, date, discharge), lithology/well-construction logs, rainfall station + daily rainfall tables, water-quality tables.
- **Model:** PGNN-LSTM — 2-layer GCN over a 52-well spatial graph (edges weighted by distance + geology match + block match) feeding into one of 4 geology-stratified LSTMs (Weathered/Fractured/Massive/Other), then temporal self-attention, then a 12-month forecast head from a 24-month lookback window. Custom physics loss (Darcy smoothness + monsoon water-balance + mass-conservation clamp).
- **Real measured performance** (from actual run logs, not estimates):

| Variant | RMSE (m) | R² | NSE | Wells R²>0.7 |
|---|---|---|---|---|
| v2 no-rain (28k params) | 3.70 | 0.43 | 0.43 | 10/41 |
| **v3 no-rain (243k params)** | **3.40** | **0.65** | **0.65** | **16/37** |
| Rainfall-enhanced final (254k params) | 3.76 | 0.56 | 0.56 | 4/37 |

- **Decision:** We ship **v3 (no-rain)** as the production model for v1. It has the best R²/RMSE and the fewest failure modes. The rainfall-enhanced variant underperforms it (likely overfitting on ~52 wells × ~300 months) — it is *not* production-ready and is parked as an R&D branch, not built into the app now.
- **Known model weaknesses to design around:** Fractured-basalt wells are the weakest (R²≈0.50) — the UI must show uncertainty, never a bare number. The model's graph is fixed to 52 known wells; arbitrary GPS points need a defined strategy (Section 4.5).
- **Known data weaknesses to fix before anything else:** lat/longs are unparsed DMS strings and were never validated (the notebook's own map script used placeholder coordinates with a comment admitting it); there is no documented, repeatable path from `IndorePZ.mdb` → the notebook's `Book2.xlsx` input.

---

## 1. Product decision: what we're actually building

A web app, CLART-inspired in presentation (map-first, color-coded, location-driven) but forecasting-driven in substance (not static overlays). Concretely:

1. A **map view** of all monitored wells, colored by projected 12-month trend (Stable / Watch / Critical).
2. A **well detail view**: historical hydraulic head chart, 12-month forecast with uncertainty band, aquifer zone, block/village context.
3. A **location-based view**: user provides/allows GPS (or clicks the map) → app finds/creates the nearest relevant forecast, same as CLART's "stand here, see the answer" pattern.
4. A lightweight **rule-based recommendation layer** on top of the forecast (see 4.6) — this is our answer to CLART's recommendation function, and it's explicitly a v1 heuristic to be refined with domain experts, not a black-box output.
5. Admin/data-refresh path (Phase 5) — not user-facing v1, but designed for from the start so new readings aren't a re-engineering event.

**Explicitly out of scope for v1:** native mobile, on-device inference, live weather-forecast integration, multi-district support. All four are real Phase-2+ items (Section 8).

---

## 2. Additional data to source (my calls, with reasoning)

The two files you gave me are the core, but a CLART-comparable product benefits from a few supporting layers. I'm deciding to source these because they're free, well-documented, and directly upgrade specific weak points identified above — not "nice to have" padding.

| Data | Source | Why | Priority |
|---|---|---|---|
| **Village/block/tahsil boundaries for Indore district** | OpenStreetMap via Overpass API, or Survey of India open layers | Needed for the map UI to draw administrative context (CLART does this) and for spatial joins in PostGIS | High — needed for MVP map |
| **SRTM 30m DEM for Indore district** | OpenTopography.org or Bhuvan (NRSC/ISRO) | Enables a slope layer — directly useful for the recommendation heuristic (steep slope = faster runoff = different recharge behavior) and is one of CLART's actual input layers | Medium — needed for recommendation layer v1.1, not blocking map MVP |
| **Land Use/Land Cover (LULC) for Indore district** | Bhuvan (NRSC/ISRO) LULC service, or ESA WorldCover (free, global, 10m) | CLART uses LULC directly; also improves the recommendation heuristic (agricultural vs. built-up vs. forest changes recharge assumptions) | Medium |
| **Historical/normal rainfall backfill & recent-month rainfall updates** | IMD 0.25°×0.25° gridded daily rainfall (imdpune.gov.in, 1901–present, free for research use) for backfill/normals; **Open-Meteo Historical Weather API** (ERA5-based, free, no API key, simple JSON, good for the recent-months feed) for keeping the model's 24-month input window current between mdb refreshes | High for keeping forecasts current, since the model needs recent rainfall in its input window even though it doesn't need *future* rainfall forecasts (see 4.4) |
| **CGWB/India-WRIS aquifer maps for Indore district** | India-WRIS portal (public) | Cross-validation for our own aquifer-zone classification (currently derived only from lithology logs) — a sanity check, not a dependency | Low — validation only |

**What we do *not* need to source:** weather *forecast* data. The model consumes rainfall as a feature over its historical input window and emits all 12 months in one forward pass — it does not autoregress on future rainfall. This was a real error in an earlier draft plan and is corrected here (see decision log, Section 9).

---

## 3. Locked architecture

```
┌────────────────────────────────────────────────────────────────┐
│ FRONTEND — Next.js (React) + Tailwind CSS, built PWA-ready      │
│ Leaflet for the map (OSS, no vendor key needed to start)        │
│ Pages: Map, Well Detail, About/Methodology                      │
│ Hosting: Vercel                                                 │
└───────────────────────────┬──────────────────────────────────────┘
                             │ REST/JSON, versioned (/api/v1/...)
┌───────────────────────────▼──────────────────────────────────────┐
│ BACKEND — FastAPI (Python)                                       │
│ Routers: wells, forecast, zones, admin (later)                   │
│ Stateless; every response cache-friendly (mobile-ready payloads) │
│ Hosting: Render (or Railway) — single container to start         │
└───────┬───────────────────────────────────┬──────────────────────┘
        │                                   │
┌───────▼─────────────────────┐   ┌─────────▼─────────────────────┐
│ DATABASE                    │   │ MODEL SERVICE (in-process to   │
│ PostgreSQL + PostGIS         │   │ start; extract to its own      │
│ Tables: wells, readings,     │   │ service only if load requires) │
│ rainfall, lithology, zones,  │   │ Loads pgnn_v3.pt (TorchScript  │
│ boundaries (geom)            │   │ export), preprocessing module  │
└───────────────────────────────┘   │ shared with training code      │
        ▲                           └─────────────────────────────────┘
        │
┌───────┴───────────────────────┐
│ ETL / DATA PIPELINE            │
│ One-time: mdb → Postgres        │
│ Recurring (monthly/on-demand): │
│ new readings, rainfall refresh │
└─────────────────────────────────┘
```

**Why these choices, decided (not offered as options):**
- FastAPI + PostgreSQL/PostGIS: Python-native, works directly with the PyTorch model without a language boundary, PostGIS gives free "nearest well to this point" queries instead of hand-rolled distance math.
- Next.js over plain React: gets SSR + easy PWA config for free, which pays forward directly into the mobile-later requirement without committing to it now.
- Leaflet over Mapbox to start: no API key/billing setup needed to get moving; can swap to Mapbox later purely for styling if desired — not a structural decision.
- In-process model service, not a separate microservice, for v1: 52 wells and modest traffic don't justify the operational overhead of a second service yet. Revisit only if inference load or team split (an ML-only teammate wanting to redeploy independently) makes it worthwhile.

---

## 4. Data flow (locked)

### 4.1 One-time ETL (Phase 1 output)
`IndorePZ.mdb` → parser script → cleaned, validated tables loaded into PostgreSQL. DMS lat/long strings parsed to decimal degrees and validated against Indore district's known bounding box (~22.4–23.1°N, 75.4–76.1°E) as a sanity filter — any well falling outside gets flagged for manual review, not silently trusted.

### 4.2 Recurring ingestion (Phase 5, not v1-blocking)
New manual/DWLR readings + Open-Meteo rainfall pulled on a schedule, appended to Postgres. Model is **not** retrained automatically — retraining is a deliberate, versioned action (Section 6), not a cron job, given the small dataset and the real risk of silently degrading the model the way the rainfall variant already did once.

### 4.3 Request-time flow (map click or GPS)
1. Frontend sends lat/long (from GPS or map click) to `GET /api/v1/forecast?lat=..&lon=..`.
2. Backend does a PostGIS nearest-neighbor query against the 52 well nodes.
3. **If within ~2km of an existing well:** use that well's node directly (real graph membership, most reliable).
4. **If farther:** dynamically extend the graph — compute this point's edges to existing nodes using the *same* distance/geology-match/block-match rule the model was trained with (Section 4.5), run one extra forward pass through the (shared-weight) GCN layers with the enlarged adjacency matrix. No retraining needed — GCN weights are shared across nodes by construction.
5. Backend pulls that well's/point's last 24 months of readings + rainfall, runs the shared preprocessing module (scaling, sequence building, zone lookup), calls the model, applies MC-dropout for an uncertainty band.
6. Recommendation heuristic (4.6) applied to the forecast.
7. JSON returned: `{well_id, forecast: [{month, head_m, lower, upper}], zone, trend_label, recommendation}`.
8. Frontend renders map marker color + detail chart.

### 4.4 Why no live weather-forecast API is required
The model's 12-month output is produced in a single forward pass from a 24-month *historical* input window — it is not autoregressive on future rainfall. What actually matters is keeping that 24-month window's **most recent months current** as real time moves forward past the mdb's last export. That's a data-freshness job (pull last N months of actual rainfall from Open-Meteo), not a forecasting-integration job. This corrects an earlier draft's assumption and is locked here.

### 4.5 Arbitrary-GPS-point handling
This is the one piece of "make CLART-like GPS lookup actually work" that's real engineering, not a one-liner, and it's scoped explicitly as its own task in Phase 3 rather than assumed away.

### 4.6 Recommendation heuristic (v1, rule-based, explicitly provisional)
Not derived from either input file — this is new logic I'm adding to close the "CLART gives a recommendation, our model gives a number" gap, designed to be simple and legible so your team can sanity-check and override it easily:

```
if forecast_12mo_change <= -3.0 m  → "Critical" (red)   → suggest recharge structure priority
elif forecast_12mo_change <= -1.0 m → "Watch" (amber)    → suggest monitoring frequency increase
else                                → "Stable" (green)
Modifiers: Fractured-zone wells get a wider uncertainty disclaimer flagged in the UI
           (their R² ≈ 0.50 vs 0.61–0.65 for other zones — this is shown to the user, not hidden)
```
This table is a starting point meant to be reviewed with your team/domain experts before go-live — flagged explicitly as v1, not treated as validated science.

---

## 5. Database schema (locked, to be created in Phase 1)

```sql
wells (
  well_id TEXT PRIMARY KEY,           -- e.g. 'ASIND-001-PZ'
  well_type TEXT, agency TEXT, district TEXT, tahsil TEXT,
  block TEXT, village TEXT,
  geom GEOGRAPHY(POINT, 4326),        -- parsed from DMS, validated
  elevation_m NUMERIC,
  command_area NUMERIC,
  aquifer_zone TEXT,                  -- computed: Weathered/Fractured/Massive/Other
  dwlr_installed BOOLEAN, dwlr_no TEXT
)

readings (
  id SERIAL PRIMARY KEY,
  well_id TEXT REFERENCES wells,
  date DATE,
  depth_bgl_m NUMERIC,
  head_msl_m NUMERIC,                 -- computed: elevation - depth
  source TEXT                         -- 'mdb_import' | 'dwlr' | 'manual'
)

lithology_logs (
  well_id TEXT REFERENCES wells,
  depth_to_m NUMERIC, lyr_id TEXT, lithology TEXT,
  colour TEXT, texture TEXT
)

rainfall_stations (
  station_name TEXT PRIMARY KEY,
  geom GEOGRAPHY(POINT, 4326)
)

rainfall_readings (
  station_name TEXT REFERENCES rainfall_stations,
  date DATE, rainfall_mm NUMERIC,
  source TEXT                         -- 'mdb_import' | 'open_meteo'
)

admin_boundaries (
  id SERIAL PRIMARY KEY,
  level TEXT,                         -- 'block' | 'village'
  name TEXT, geom GEOGRAPHY(POLYGON, 4326)
)

model_versions (
  version_id TEXT PRIMARY KEY,        -- e.g. 'pgnn_v3_2025_08'
  trained_on DATE, rmse NUMERIC, r2 NUMERIC,
  artifact_path TEXT, is_active BOOLEAN
)
```

---

## 6. Model productionization plan (locked)

1. Extract cell 10's data pipeline (loading, MSL conversion, aquifer classification, graph construction, node features) into a standalone `preprocessing.py` — this module is imported by **both** the training script and the serving code, so they can never silently drift apart the way `Book2.xlsx` and the mdb already have.
2. Extract the `PGNN_LSTM` model class as-is into `model.py`.
3. Re-run training using the **v3 configuration** (243k params, no rainfall) as the locked baseline, save via `torch.jit.script` or export to ONNX for a dependency-light serving path.
4. Write `inference.py`: `predict(well_id_or_point, as_of_date) -> forecast + uncertainty`, wrapping MC-dropout (already prototyped in the notebook's Cell G) as the uncertainty source.
5. Record the run's metrics into the `model_versions` table — every deployed model is versioned and traceable, not a loose `.pt` file on someone's drive.
6. The rainfall-enhanced variant is kept in a separate `experimental/` path in the repo, not wired to the API, until/unless your ML teammates improve on it.

---

## 7. Repository & delivery structure

```
groundwater-app/
├── etl/                  # mdb parser, coordinate validator, rainfall backfill scripts
├── ml/
│   ├── preprocessing.py  # shared training+serving logic
│   ├── model.py          # PGNN_LSTM class
│   ├── train.py          # locked v3 training entrypoint
│   ├── inference.py      # predict() used by API
│   └── experimental/     # rainfall variant, future improvements
├── backend/               # FastAPI app, routers, PostGIS queries
├── frontend/               # Next.js app
├── infra/                  # Docker Compose, deployment configs
└── docs/                   # this plan, API contract, data dictionary
```

---

## 8. Phased roadmap (locked, with what "done" means per phase)

**Phase 1 — Data foundation**
Parse & validate `IndorePZ.mdb` → PostgreSQL/PostGIS. Parse DMS coordinates, validate against district bounding box. Backfill rainfall via Open-Meteo where mdb data is stale.
*Done when:* every well has a validated lat/long, every table above is populated and queryable.

**Phase 2 — Model productionization**
Extract shared preprocessing, lock v3 as production model, build `inference.py`, version the artifact.
*Done when:* `predict(well_id)` returns correct forecasts matching the notebook's own evaluation numbers within rounding.

**Phase 3 — Backend API**
Build FastAPI routers, PostGIS nearest-neighbor + dynamic graph-extension logic for arbitrary GPS points, recommendation heuristic.
*Done when:* `/api/v1/forecast` works for both a known well ID and an arbitrary lat/long inside the district.

**Phase 4 — Frontend**
Map view, well detail view, GPS-based lookup, PWA manifest configured (even though offline mode isn't built yet — free to enable now).
*Done when:* a user can open the map, click any point in Indore district, and see a forecast with uncertainty and a recommendation label.

**Phase 5 — Deployment & recurring ingestion**
Docker Compose, deploy backend+DB to Render, frontend to Vercel. Build the (manual-trigger, not automatic) recurring ingestion job.
*Done when:* the app is live at a real URL and new readings can be added without a redeploy.

**Phase 6 — Validation loop**
Share with your teammates/domain experts specifically on: the recommendation thresholds (Section 4.6), the fractured-zone uncertainty framing, and whether the rainfall-variant is worth revisiting.

**Phase 7 (later, explicitly deferred) — Mobile**
Two realistic sub-paths, decided at this phase, not now: (a) ship the PWA as installable — fastest, reuses everything; (b) build React Native app against the same API for a more native feel. **On-device inference is out of scope** even at this phase unless your team specifically wants to invest in ONNX Mobile/TFLite conversion — offline mode should instead mean "last-synced forecasts cached locally," which is honest about what a ~250K-parameter GNN+LSTM can realistically do on a phone without dedicated ML-mobile work.

---

## 9. Decision log (so nothing here gets re-argued from memory later)

- **Production model = v3 no-rain**, not the "final" rainfall-enhanced one, despite its name — chosen strictly on measured R²/RMSE, not on which one is labeled "final" in the notebook.
- **No live weather-forecast API needed** for core prediction — only recent-actuals refresh. (An earlier draft plan got this wrong; corrected here.)
- **Forecast horizon is 12 months**, not to 2040 — the "2040" figure that appeared elsewhere in the notebook was a hardcoded placeholder in an unrelated demo map script with fabricated coordinates, not a model capability.
- **Arbitrary GPS points get real graph-extension handling**, not just "snap to nearest well" — scoped as its own Phase 3 task given its real complexity.
- **Recommendation thresholds are a new v1 heuristic**, explicitly not derived from either source file, and explicitly flagged to the user as provisional pending domain review.
- **Mobile is Phase 7, API-ready from Phase 3 onward** — no separate mobile backend will ever be needed.

---

## 10. What I still need from you / your team (not blocking, but real)

- Sign-off on the recommendation thresholds in 4.6 once we're at Phase 6, from whoever on your team has hydrogeology judgment.
- A decision on hosting budget (Render/Vercel free tiers are enough for MVP traffic; flag if you expect real field-scale usage sooner).
- Whether the rainfall-variant model is worth a dedicated retraining effort — that's your ML teammates' call, not something I should decide unilaterally.
