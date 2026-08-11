# System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                     http://localhost:3000                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Requests
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                      FRONTEND CONTAINER                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Next.js 14 (React)                                        │ │
│  │  ├── pages/index.tsx        (Main UI)                      │ │
│  │  ├── components/Map.tsx     (Leaflet map)                  │ │
│  │  ├── components/Chart.tsx   (Recharts)                     │ │
│  │  └── lib/api.ts             (API client)                   │ │
│  │                                                              │ │
│  │  Port: 3000                                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ REST API Calls
                             │ GET /api/v1/wells
                             │ GET /api/v1/forecast/well/{id}
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                      BACKEND CONTAINER                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  FastAPI (Python 3.11)                                     │ │
│  │  ├── routers/wells.py       (Well endpoints)               │ │
│  │  ├── routers/forecast.py    (Forecast endpoints)           │ │
│  │  ├── services/                                              │ │
│  │  │   ├── statistical_trend.py  (Forecasting logic)         │ │
│  │  │   ├── recommendation.py     (Classification)            │ │
│  │  │   └── graph.py              (Future: PGNN-LSTM)         │ │
│  │  └── db.py                  (Database connection pool)     │ │
│  │                                                              │ │
│  │  Port: 8000                                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ SQL Queries (asyncpg)
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                      DATABASE CONTAINER                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL 16 + PostGIS 3.4                               │ │
│  │                                                              │ │
│  │  Tables:                                                    │ │
│  │  ├── wells           (1,196 rows)                          │ │
│  │  │   ├── well_id (PK)                                      │ │
│  │  │   ├── lat_raw, lon_raw                                  │ │
│  │  │   ├── geom (PostGIS POINT)                              │ │
│  │  │   ├── elevation_m                                       │ │
│  │  │   ├── block, aquifer_zone                               │ │
│  │  │   └── trend_label (cached)                              │ │
│  │  │                                                          │ │
│  │  ├── readings       (139,837 rows)                         │ │
│  │  │   ├── well_id (FK)                                      │ │
│  │  │   ├── date                                              │ │
│  │  │   ├── depth_bgl_m                                       │ │
│  │  │   └── head_msl_m                                        │ │
│  │  │                                                          │ │
│  │  └── litho          (1,048+ rows)                          │ │
│  │      ├── well_id (FK)                                      │ │
│  │      ├── depth_from_m, depth_to_m                          │ │
│  │      └── lithology                                         │ │
│  │                                                              │ │
│  │  Port: 5432                                                 │ │
│  │  Volume: pgdata (persistent)                               │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

### 1. User Interaction Flow

```
User opens app
    ↓
Frontend loads map component
    ↓
API Call: GET /api/v1/wells
    ↓
Backend queries: SELECT well_id, lat, lon, trend_label FROM wells
    ↓
Database returns 1,196 wells with cached trend_label
    ↓
Frontend renders colored markers on map
    ↓
User clicks a well marker
    ↓
Frontend calls: GET /api/v1/forecast/well/{well_id}
    ↓
Backend:
  1. Fetches well metadata
  2. Queries readings: SELECT date, head_msl_m WHERE well_id = ?
  3. Runs statistical forecast (linear regression)
  4. Classifies trend (Critical/Watch/Stable)
  5. Generates recommendation text
    ↓
Frontend displays:
  - Well info card
  - Trend status (color-coded)
  - Historical chart (recharts)
  - 12-month forecast chart
  - Recommendation text
```

---

## ETL Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES (Legacy)                         │
│                                                                  │
│  GW_Data/Water Level/                                           │
│  ├── IndorePZ.mdb        ┐                                      │
│  ├── JBP-OW.MDB          │                                      │
│  ├── SGWL-PZ.MDB         │  21 databases                        │
│  └── ... (18 more)       ┘                                      │
│                                                                  │
│  GW_Data/Water Quality/                                         │
│  └── ... (13 databases)                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Step 1: Extract
                         │ Tool: mdb-export (MDB Tools)
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                    CSV INTERMEDIATES                             │
│                                                                  │
│  temp_*.csv files:                                              │
│  ├── WellData tables → wells metadata                          │
│  ├── Readings tables → water level measurements                │
│  └── Litho tables    → lithology data                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Step 2: Parse & Clean
                         │ Tool: parse_coordinates.py
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                    CLEANED CSV FILES                             │
│                                                                  │
│  data/                                                          │
│  ├── wells.csv          (1,196 rows)                           │
│  ├── water_levels.csv   (139,837 rows)                         │
│  └── litho.csv          (1,048+ rows)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Step 3: Load
                         │ Tool: load_to_postgres.py
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                    POSTGRESQL DATABASE                           │
│                                                                  │
│  Tables: wells, readings, litho                                 │
│  PostGIS geometries computed from lat/lon                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Step 4: Enrich
                         │ Tool: fetch_elevations.py
                         │ API: Open-Elevation
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                  ENRICHED DATABASE                               │
│                                                                  │
│  Wells now have:                                                │
│  ├── elevation_m (from SRTM API)                               │
│  └── head_msl_m computed for readings                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Step 5: Pre-compute Trends
                         │ Tool: sync_trends.sh
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                  PRODUCTION DATABASE                             │
│                                                                  │
│  Wells now have:                                                │
│  └── trend_label cached (Critical/Watch/Stable/Unknown)        │
│  └── trend_updated_at timestamp                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Forecasting Algorithm Flow

```
Input: well_id
    ↓
┌─────────────────────────────────────┐
│ 1. Fetch Historical Readings       │
│    SELECT date, head_msl_m          │
│    WHERE well_id = ?                │
│    ORDER BY date DESC               │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ 2. Check Data Sufficiency           │
│    ├─ <3 readings?   → NO_DATA     │
│    ├─ 3-23 readings? → LIMITED     │
│    └─ ≥24 readings?  → FULL        │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ 3. Compute Linear Trend             │
│    y = mx + b                       │
│    m = slope (meters/year)          │
│    b = intercept                    │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ 4. Classify Trend                   │
│    if slope ≤ -2.0:   CRITICAL     │
│    elif slope ≤ -0.5: WATCH        │
│    else:              STABLE        │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ 5. Generate 12-Month Forecast       │
│    For month in [0..11]:            │
│      forecast[month] = m×month + b  │
│      lower = forecast × 0.8         │
│      upper = forecast × 1.2         │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ 6. Create Recommendation Text       │
│    Based on classification:         │
│    ├─ Critical: "Immediate action"  │
│    ├─ Watch: "Monitor closely"      │
│    └─ Stable: "Continue monitoring" │
└────────────┬────────────────────────┘
             │
             ↓
Output: ForecastResponse JSON
```

---

## Database Schema (Detailed)

### wells table
```sql
CREATE TABLE wells (
    well_id TEXT PRIMARY KEY,           -- "BPL-PZ-08"
    district TEXT,                      -- "Bhopal"
    block TEXT,                         -- "Barasia"
    village TEXT,                       -- "Berkhedi Kala"
    lat_raw TEXT,                       -- "23.637778" (stored as text)
    lon_raw TEXT,                       -- "77.433611"
    elevation_m FLOAT,                  -- 516.0 (MSL)
    aquifer_zone TEXT,                  -- Currently NULL (was "NaN")
    geom GEOMETRY(Point, 4326),         -- PostGIS geometry
    trend_label TEXT,                   -- "Critical" | "Watch" | "Stable" | "Unknown"
    trend_updated_at TIMESTAMP,         -- Cache timestamp
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_wells_geom ON wells USING GIST(geom);
CREATE INDEX idx_wells_trend ON wells(trend_label);
```

### readings table
```sql
CREATE TABLE readings (
    well_id TEXT REFERENCES wells(well_id),
    date DATE NOT NULL,
    depth_bgl_m FLOAT,                  -- Depth below ground level
    head_msl_m FLOAT,                   -- Hydraulic head (elevation - depth)
    PRIMARY KEY (well_id, date)
);

-- Indexes
CREATE INDEX idx_readings_well_date ON readings(well_id, date DESC);
CREATE INDEX idx_readings_date ON readings(date);
```

### litho table
```sql
CREATE TABLE litho (
    well_id TEXT REFERENCES wells(well_id),
    depth_from_m FLOAT,                 -- Layer start depth
    depth_to_m FLOAT,                   -- Layer end depth
    lithology TEXT,                     -- "Weathered Basalt"
    PRIMARY KEY (well_id, depth_from_m)
);

-- Indexes
CREATE INDEX idx_litho_well ON litho(well_id);
```

---

## API Architecture

### Endpoint Structure

```
/api/v1/
├── /wells
│   ├── GET /                    → List all wells with trend labels
│   └── GET /{well_id}/history   → Historical readings
│
├── /forecast
│   ├── GET /well/{well_id}      → 12-month forecast for specific well
│   └── GET /?lat=X&lon=Y        → Forecast for arbitrary point
│
└── /zones (Future)
    └── GET /{zone_id}           → Zone-level aggregates
```

### Response Models (Pydantic)

```python
# WellSummary
{
    "well_id": str,
    "lat": float,
    "lon": float,
    "block": Optional[str],
    "aquifer_zone": Optional[str],
    "trend_label": Optional[str]  # "Critical" | "Watch" | "Stable" | None
}

# ForecastResponse
{
    "well_id": str,
    "matched_existing_well": bool,
    "distance_to_nearest_well_km": Optional[float],
    "aquifer_zone": str,
    "forecast": List[ForecastPoint],
    "trend_label": str,
    "recommendation": str,
    "model_version": str,
    "caveat": Optional[str]
}

# ForecastPoint
{
    "month_index": int,        # 0-11
    "head_msl_m": float,       # Predicted head
    "lower_m": float,          # Lower confidence bound
    "upper_m": float           # Upper confidence bound
}
```

---

## Frontend Component Tree

```
App (pages/index.tsx)
├── GroundwaterMap (components/Map.tsx)
│   ├── MapContainer (react-leaflet)
│   │   ├── TileLayer (OpenStreetMap)
│   │   └── CircleMarker × 1,196
│   │       └── Popup (well details)
│   └── Error State (if API fails)
│
└── Sidebar
    ├── Header
    │   ├── "Madhya Pradesh"
    │   ├── "Groundwater Forecast"
    │   └── Instructions
    │
    ├── Well Info Card (if selected)
    │   ├── Well ID / Coordinates
    │   └── Block Name
    │
    ├── Trend Status Card
    │   ├── Status Badge (color-coded)
    │   └── Recommendation Text
    │
    ├── Historical Chart
    │   └── ResponsiveContainer
    │       └── LineChart (recharts)
    │
    ├── Forecast Chart
    │   └── ForecastChart
    │       └── LineChart with confidence bands
    │
    └── Data Quality Indicator
        └── (only shown for low-confidence forecasts)
```

---

## Deployment Architecture (Docker Compose)

```yaml
services:
  db:
    image: postgis/postgis:16-3.4
    ports: ["127.0.0.1:5432:5432"]
    volumes:
      - pgdata:/var/lib/postgresql/data
      - schema.sql:/docker-entrypoint-initdb.d/
    healthcheck:
      test: pg_isready
      interval: 5s
      retries: 10
    
  backend:
    build: ../backend
    ports: ["8000:8000"]
    depends_on:
      db: {condition: service_healthy}
    volumes:
      - ../backend/app:/app/backend/app  # Hot reload
    environment:
      DATABASE_URL: postgresql://gwuser:changeme@db:5432/groundwater
    
  frontend:
    build: ../frontend
    ports: ["3000:3000"]
    depends_on: [backend]
    build_args:
      NEXT_PUBLIC_API_BASE: http://localhost:8000

volumes:
  pgdata:  # Persistent database storage
```

### Container Communication
- **Frontend → Backend**: Via host machine (`localhost:8000`)
  - Browser makes requests, not the container
  - That's why `NEXT_PUBLIC_API_BASE=http://localhost:8000` works
- **Backend → Database**: Via Docker network (`db:5432`)
  - Container-to-container DNS resolution
  - That's why `DATABASE_URL=...@db:5432/...` works

---

## Security Architecture (Current State)

### ⚠️ Development Mode
```
Authentication:     None
Authorization:      None
HTTPS:              No (HTTP only)
Database Access:    Default password
CORS:               Allow all origins
Rate Limiting:      None
Input Validation:   Basic (Pydantic)
SQL Injection:      Protected (parameterized queries)
XSS Protection:     React default escaping
```

### 🔒 Production Hardening (TODO)
```
Authentication:     JWT tokens
Authorization:      Role-based access control
HTTPS:              SSL/TLS certificates
Database Access:    Strong passwords + restricted network
CORS:               Whitelist specific domains
Rate Limiting:      100 req/min per IP
Input Validation:   Comprehensive (Pydantic + custom)
Audit Logging:      All API calls logged
Monitoring:         Prometheus + Grafana
Backups:            Daily automated backups
```

---

## Scalability Considerations

### Current Capacity
```
Database Size:      ~50 MB (1,196 wells + 139K readings)
API Throughput:     ~100 req/sec (single backend container)
Concurrent Users:   ~50-100 users
Map Performance:    Good up to 5,000 markers
```

### Scaling Strategy

#### Horizontal Scaling
```
                    ┌─── backend-1 ───┐
Load Balancer  ────┼─── backend-2 ───┤──── Database
(nginx)             ├─── backend-3 ───┤    (Primary)
                    └─── backend-N ───┘         │
                                                 │ Replication
                                            Database
                                            (Replica - read-only)
```

#### Caching Layer
```
Browser → CDN (static assets) → Frontend
   │
   └→ API Gateway → Redis Cache → Backend → Database
```

#### Database Optimization
```sql
-- Partition readings table by year
CREATE TABLE readings_2024 PARTITION OF readings 
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- Materialized view for aggregates
CREATE MATERIALIZED VIEW district_summary AS
SELECT ...
REFRESH MATERIALIZED VIEW district_summary;
```

---

## Monitoring & Observability (Future)

### Metrics to Track
```
Application Metrics:
├── API response time (p50, p95, p99)
├── Error rate (4xx, 5xx)
├── Forecast computation time
└── Cache hit rate

System Metrics:
├── CPU usage per container
├── Memory usage per container
├── Disk I/O (database)
└── Network traffic

Business Metrics:
├── Wells viewed per day
├── Forecasts generated per day
├── Critical wells identified
└── User engagement (time on site)
```

### Proposed Stack
```
Application → Prometheus (metrics)
           → Loki (logs)
           → Jaeger (tracing)
                ↓
           Grafana (visualization)
                ↓
           AlertManager (alerts)
```

---

## Future Architecture (ML Model Integration)

### Planned: PGNN-LSTM Model

```
Current: Statistical Trend
    ↓
Future: Hybrid Approach
    ├── PGNN-LSTM (if available)
    │   ├── Graph Neural Network layer
    │   ├── LSTM for time series
    │   └── Trained on 1,092 wells
    │
    └── Statistical Fallback
        └── For wells with limited data
```

### Model Serving Architecture
```
Frontend
    ↓
Backend API
    ↓
┌───────────────────────────────┐
│  Model Router                 │
│  ├─ Check data availability   │
│  ├─ If sufficient → ML model  │
│  └─ Else → Statistical model  │
└───────────────────────────────┘
    ↓
┌───────────────────────────────┐
│  ML Model (TorchServe)        │
│  ├── Load model.pt            │
│  ├── Preprocess features      │
│  ├── Run inference            │
│  └── Post-process predictions │
└───────────────────────────────┘
```

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**For**: System architecture reference
