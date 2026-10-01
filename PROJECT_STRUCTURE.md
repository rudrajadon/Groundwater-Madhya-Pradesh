# Project Structure Documentation

Detailed breakdown of the Madhya Pradesh Groundwater Monitoring System architecture.

## Directory Overview

```
groundwater-app/
├── backend/              # Backend API (FastAPI + Python)
├── frontend/            # Frontend web app (Next.js + React)
├── ml/                  # Machine learning models and training
├── etl/                 # ETL pipelines for data processing
├── data/               # Processed CSV data files
├── raw_data/           # Original source data (MDB files)
├── shapefile_data/     # Geographic shapefiles
├── scripts/            # Utility scripts
├── docs/               # Additional documentation
├── infra/              # Infrastructure as code
├── logs/               # Application logs
└── _archive/           # Archived/deprecated files
```

## Backend (`/backend`)

FastAPI REST API serving groundwater data and ML predictions.

### Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization, CORS, lifespan
│   ├── db.py                # Database connection, SQLAlchemy engine
│   ├── schemas.py           # Pydantic models for request/response
│   │
│   ├── routers/            # API endpoint definitions
│   │   ├── __init__.py
│   │   ├── wells.py        # /api/v1/wells endpoints
│   │   ├── forecast.py     # /api/v1/forecast endpoints
│   │   ├── stress_map.py   # /api/v1/stress-map endpoints
│   │   ├── exports.py      # /api/v1/exports (PDF reports)
│   │   ├── zones.py        # /api/v1/zones (aquifer zones)
│   │   ├── districts.py    # /api/v1/districts
│   │   └── location_predictor.py  # /api/v1/predict endpoints
│   │
│   ├── services/           # Business logic layer
│   │   ├── recommendation.py    # Trend classification, recommendations
│   │   ├── report_generator.py  # PDF report generation
│   │   └── statistical_trend.py # Fallback trend analysis
│   │
│   └── data/              # Static data files
│       └── mp_districts_simplified.geojson  # District boundaries
│
├── Dockerfile             # Container definition for deployment
├── requirements.txt       # Python dependencies
└── README.md             # Backend-specific docs
```

### Key Components

#### `main.py`
- Initializes FastAPI application
- Configures CORS middleware
- Loads ML model at startup (lifespan event)
- Includes all routers

#### `db.py`
- Creates SQLAlchemy engine with connection pooling
- Defines database session dependency
- Uses async-compatible psycopg3 driver

#### `routers/`
Each router handles a specific domain:
- **wells.py:** Well locations, history, rainfall
- **forecast.py:** ML predictions, statistical fallback
- **stress_map.py:** District-level aggregations, GeoJSON
- **exports.py:** PDF report generation
- **zones.py:** Aquifer zone analysis
- **districts.py:** District list and metadata

#### `services/`
Reusable business logic:
- **recommendation.py:** Classifies trends as Critical/Watch/Stable
- **report_generator.py:** Creates PDF reports with charts
- **statistical_trend.py:** Linear regression for wells without ML

## Frontend (`/frontend`)

Next.js web application with React and Leaflet.

### Structure
```
frontend/
├── pages/
│   ├── _app.tsx              # Next.js app wrapper
│   ├── _document.tsx         # HTML document structure
│   ├── index.tsx             # Main map page
│   ├── about.tsx             # About page
│   ├── stress-map.tsx        # District stress map page
│   └── districts/[id].tsx    # District detail page (optional)
│
├── components/
│   ├── Map.tsx               # Main Leaflet map with well markers
│   ├── StressMap.tsx         # District choropleth map
│   ├── WellDetailPopup.tsx   # Well info modal
│   ├── MobileWellDrawer.tsx  # Mobile-responsive well drawer
│   ├── ForecastChart.tsx     # 12-month forecast visualization
│   ├── ExportModal.tsx       # Export options dialog
│   ├── DistrictSummary.tsx   # District statistics component
│   └── Navbar.tsx            # Navigation bar
│
├── styles/
│   ├── globals.css           # Global styles, Leaflet overrides
│   └── Home.module.css       # Page-specific styles
│
├── public/
│   ├── geo/
│   │   ├── mp_districts.geojson           # Full district boundaries
│   │   └── mp_districts_simplified.geojson # Simplified for frontend
│   ├── favicon.ico
│   └── images/              # Static images
│
├── next.config.js           # Next.js configuration (basePath, env)
├── package.json             # npm dependencies
├── tsconfig.json            # TypeScript configuration
└── .env.local              # Local environment variables (gitignored)
```

### Key Components

#### `pages/index.tsx`
- Main application entry point
- Renders interactive map with well markers
- Handles well selection and detail popup
- Responsive layout (desktop sidebar, mobile drawer)

#### `components/Map.tsx`
- Leaflet map integration
- Well markers color-coded by trend
- Clustering for performance
- Click handlers for well selection

#### `components/StressMap.tsx`
- District-level choropleth
- Color scale based on risk level
- Click to zoom into district
- Optional well-level heat map overlay

#### `components/ForecastChart.tsx`
- Recharts line chart
- 12-month forecast with confidence intervals
- Historical data overlay
- Responsive design

## Machine Learning (`/ml`)

PGNN-LSTM model for groundwater forecasting.

### Structure
```
ml/
├── models/
│   ├── __init__.py
│   ├── pgnn_lstm.py         # PGNN-LSTM architecture
│   ├── graph_builder.py     # Graph construction from wells
│   └── attention.py         # Attention mechanism
│
├── artifacts/               # Trained model outputs
│   ├── model_metadata.json  # Training metadata, hyperparameters
│   ├── best_model.pth       # Model weights
│   ├── graph.pkl           # Pre-built graph structure
│   └── scalers/            # Per-well MinMax scalers
│       ├── WELL001.pkl
│       ├── WELL002.pkl
│       └── ...
│
├── train.py                 # Training script
├── inference.py             # Inference wrapper class
├── evaluate.py              # Model evaluation metrics
├── config.py                # Hyperparameters, paths
└── README.md               # ML-specific documentation
```

### Model Architecture

**PGNN-LSTM** (Physics-Guided Neural Network with LSTM)
- **Graph Layer:** Captures spatial dependencies between wells
- **LSTM Encoder:** Processes 24-month time series input
- **LSTM Decoder:** Generates 12-month forecast
- **Attention:** Focuses on relevant neighboring wells

**Input:** 24 months of historical water levels (head_msl_m)
**Output:** 12 months of future predictions with uncertainty

## ETL Pipelines (`/etl`)

Extract, Transform, Load scripts for data processing.

### Structure
```
etl/
├── extract_from_mdb.py      # Extract data from MDB files
├── process_wells.py         # Clean and geocode well data
├── process_readings.py      # Process water level readings
├── process_rainfall.py      # Process rainfall data
├── process_district_boundaries.py  # Generate district GeoJSON
├── fix_well_districts.py    # Assign wells to districts
└── README.md               # ETL documentation
```

### Data Flow

1. **Extract:** Read MDB files from `raw_data/groundwater/`
2. **Transform:** Clean, validate, geocode
3. **Load:** Write to `data/*.csv` and PostgreSQL

## Data Files

### Processed Data (`/data`)
```
data/
├── wells.csv                 # All wells with coordinates
├── water_levels.csv          # Historical readings
├── rainfall.csv              # Rainfall data by station
└── well_geology_classifications.csv  # Geology types
```

### Raw Data (`/raw_data`)
```
raw_data/
└── groundwater/
    ├── Water Level/         # MDB files with water level data
    │   ├── IndoreOW.mdb
    │   ├── UjjanPZ.mdb
    │   └── ...
    └── Water Quality/       # MDB files with quality data
        ├── BHOPAL_WQ.mdb
        └── ...
```

### Shapefiles (`/shapefile_data`)
```
shapefile_data/
├── madhya_pradesh_districts/   # District boundaries
│   ├── MP_DISTRICT_BDY.shp
│   ├── MP_DISTRICT_BDY.dbf
│   └── ...
└── madhya_pradesh_state/       # State boundary
    ├── MP_STATE_BDY.shp
    └── ...
```

## Scripts (`/scripts`)

Utility scripts for maintenance and deployment.

### Database Scripts (`/scripts/database`)
```
database/
├── init_db.py               # Initialize database schema
├── add_forecast_columns.py  # Add missing columns
├── update_well_trends.py    # Calculate trend labels
├── precalculate_all_forecasts.py  # Cache forecasts
├── diagnose_database.py     # Check database health
└── fix_*.py                 # Various fix scripts
```

### Data Processing (`/scripts/data_processing`)
```
data_processing/
├── load_all_wells_to_render.py   # Load wells to production
├── load_readings_only.py         # Load water level data
├── load_rainfall_to_render.py    # Load rainfall data
└── load_*.py                     # Other loading scripts
```

### Deployment (`/scripts/deployment`)
```
deployment/
├── deploy.sh                # Deploy to production
├── START_DEPLOYMENT.sh      # Initial deployment
└── PUSH_TO_GITHUB.sh       # Git push automation
```

## Database Schema

### Tables

**wells**
- Primary table for observation wells
- Columns: well_id (PK), district, geom (PostGIS), trend_label, geology_type, etc.

**readings**
- Water level measurements over time
- Columns: id (PK), well_id (FK), date, depth_bgl_m, head_msl_m
- Constraint: UNIQUE(well_id, date)

**rainfall_stations**
- Rainfall monitoring stations
- Columns: station_name (PK), geom

**rainfall_readings**
- Rainfall measurements
- Columns: id (PK), station_name (FK), date, rainfall_mm

**lithology_logs**
- Geological layer information
- Columns: id (PK), well_id (FK), depth_to_m, lithology, texture

**admin_boundaries**
- District and state boundaries
- Columns: id (PK), level, name, geom (MultiPolygon)

**model_versions**
- ML model metadata
- Columns: version_id (PK), trained_on, rmse, artifact_path

## Configuration Files

### Backend
- **Dockerfile:** Multi-stage build for production
- **requirements.txt:** Python dependencies (FastAPI, SQLAlchemy, PyTorch, etc.)
- **.env:** Environment variables (DATABASE_URL, SECRET_KEY)

### Frontend
- **next.config.js:** Base path, environment variables, build config
- **package.json:** npm dependencies (React, Next.js, Leaflet, Recharts)
- **tsconfig.json:** TypeScript compiler options
- **.env.local:** Local dev environment variables

## Archived Files (`/_archive`)

Old documentation and deprecated scripts moved here to declutter:
- Deployment guides (old versions)
- Nginx configs (if using Docker)
- Old bash scripts
- Outdated documentation

## Development Workflow

1. **Make changes** in `backend/` or `frontend/`
2. **Test locally** with hot reload
3. **Commit** to git with descriptive message
4. **Push** to GitHub
5. **Auto-deploy** via Render (backend) and Vercel (frontend)

## API Documentation

Interactive API docs available at:
- Development: http://localhost:8000/docs
- Production: https://mp-groundwater-backend.onrender.com/docs

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Monitoring

- **Backend logs:** Render dashboard
- **Frontend logs:** Vercel dashboard
- **Database:** PostgreSQL logs on Render
- **Application health:** `/health` endpoint

## Security

- **API:** CORS configured for specific origins
- **Database:** Credentials in environment variables
- **Secrets:** Never commit to git
- **HTTPS:** Enforced in production
