# Madhya Pradesh Groundwater Monitoring System

A real-time groundwater monitoring and forecasting platform for Madhya Pradesh, India. Built with Next.js, FastAPI, and PGNN-LSTM machine learning models.

## 🌊 Overview

This system monitors 1,200+ observation wells across Madhya Pradesh, providing:
- **Real-time monitoring** of groundwater levels
- **12-month forecasts** using Graph Neural Networks
- **District-level stress maps** showing groundwater risk zones
- **Interactive visualizations** with historical trends
- **Exportable reports** for decision-makers

## 🏗️ Project Structure

```
groundwater-app/
├── backend/              # FastAPI REST API
│   ├── app/
│   │   ├── routers/     # API endpoints (wells, forecast, stress-map, exports)
│   │   ├── services/    # Business logic (ML inference, reports)
│   │   ├── data/        # Static data (district boundaries GeoJSON)
│   │   └── main.py      # FastAPI application
│   ├── Dockerfile       # Backend containerization
│   └── requirements.txt # Python dependencies
│
├── frontend/            # Next.js web application
│   ├── components/      # React components (Map, Charts, Modals)
│   ├── pages/          # Next.js routes
│   ├── public/         # Static assets
│   └── styles/         # CSS styles
│
├── ml/                  # Machine learning models
│   ├── models/         # PGNN-LSTM architecture
│   ├── artifacts/      # Trained model weights
│   └── train.py        # Training pipeline
│
├── etl/                 # Data processing pipelines
│   ├── process_*.py    # ETL scripts for wells, readings, rainfall
│   └── extract_*.py    # Data extraction from MDB files
│
├── data/               # Processed data files
│   ├── wells.csv       # Well locations and metadata
│   ├── water_levels.csv # Historical water level readings
│   └── rainfall.csv    # Rainfall data
│
├── raw_data/           # Raw source data
│   └── groundwater/    # Original MDB database files
│       ├── Water Level/
│       └── Water Quality/
│
├── shapefile_data/     # Geographic boundary files
│   ├── madhya_pradesh_districts/  # District boundaries
│   └── madhya_pradesh_state/      # State boundary
│
├── scripts/            # Utility scripts
│   ├── database/       # Database initialization and maintenance
│   ├── data_processing/ # Data loading scripts
│   └── deployment/     # Deployment automation
│
├── docs/               # Documentation
├── infra/             # Infrastructure configuration
└── _archive/          # Archived files and old documentation

```

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL** 14+ with PostGIS extension
- **Docker** (optional, for containerized deployment)

### Local Development

#### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/groundwater"
export SECRET_KEY="your-secret-key"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

#### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

Frontend runs at: `http://localhost:3000/mpgroundwater/`

### Database Setup

```bash
# Initialize database schema
python scripts/database/init_db.py

# Load well data
python scripts/data_processing/load_all_wells_to_render.py

# Load water level readings
python scripts/data_processing/load_readings_only.py

# Calculate trend labels
python scripts/database/update_well_trends.py
```

## 📊 Key Features

### 1. Interactive Map
- View all 1,200+ wells on an interactive Leaflet map
- Color-coded markers by trend (Stable, Watch, Critical)
- Click wells for detailed history and forecasts
- Filter by district, aquifer type, or geology

### 2. Groundwater Forecasting
- **PGNN-LSTM model** trained on 30+ years of data
- 12-month forecasts with confidence intervals
- Graph neural network captures spatial dependencies
- Automatic trend classification (Critical/Watch/Stable)

### 3. District Stress Map
- Choropleth map showing groundwater stress by district
- Risk levels: Low, Moderate, High, Critical
- Based on percentage of critical and declining wells
- Well-level heat maps for high-resolution districts

### 4. Data Export
- Export well reports as PDF
- District summary reports
- Downloadable CSV data
- Forecast visualizations

## 🔧 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** 2.0 - ORM with async support
- **PostgreSQL + PostGIS** - Spatial database
- **Psycopg3** - PostgreSQL adapter
- **PyTorch** - Deep learning framework
- **ReportLab** - PDF generation

### Frontend
- **Next.js** 14 - React framework
- **React Leaflet** - Interactive maps
- **Recharts** - Data visualization
- **Tailwind CSS** - Utility-first styling

### Machine Learning
- **PGNN-LSTM** - Physics-guided graph neural network
- **Graph construction** from well locations and geology
- **Attention mechanism** for spatial relationships
- **LSTM encoder-decoder** for time series

## 🌐 Deployment

### Production (Render.com)

**Backend:** https://mp-groundwater-backend.onrender.com
**Frontend:** https://www.rudrajadon.in/mpgroundwater/

```bash
# Backend deploys automatically from main branch
# Render settings:
#   - Runtime: Docker
#   - Root Directory: backend/
#   - Environment: Set DATABASE_URL, SECRET_KEY

# Frontend deploys to Vercel
# Vercel settings:
#   - Framework: Next.js
#   - Root Directory: frontend/
#   - Environment: Set NEXT_PUBLIC_API_BASE
```

## 📝 API Endpoints

### Wells
- `GET /api/v1/wells` - List all wells
- `GET /api/v1/wells/{well_id}/history` - Historical readings
- `GET /api/v1/wells/{well_id}/rainfall` - Rainfall data

### Forecasts
- `GET /api/v1/forecast?lat={lat}&lon={lon}` - Forecast by location
- `GET /api/v1/forecast/well/{well_id}` - Forecast for specific well

### Stress Map
- `GET /api/v1/stress-map/geojson` - District boundaries with stats
- `GET /api/v1/stress-map/districts` - District stress levels
- `GET /api/v1/stress-map/summary` - State-level summary

### Exports
- `GET /api/v1/exports/well/{well_id}/report` - PDF report
- `GET /api/v1/exports/district/{district}/summary` - District report

## 🛠️ Maintenance

### Update Well Trends
```bash
python scripts/database/update_well_trends.py
```

### Precalculate Forecasts
```bash
python scripts/database/precalculate_all_forecasts.py
```

### Database Diagnostics
```bash
python scripts/database/diagnose_database.py
```

## 📚 Data Sources

- **Groundwater data:** Central Ground Water Board (CGWB)
- **Well locations:** MP Water Resources Department
- **Rainfall data:** India Meteorological Department (IMD)
- **District boundaries:** Survey of India

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Contributors

Developed as part of a B.Tech project at IIT Indore.

## 🔗 Links

- **Live Application:** https://www.rudrajadon.in/mpgroundwater/
- **API Documentation:** https://mp-groundwater-backend.onrender.com/docs
- **Project Repository:** [GitHub](https://github.com/rudrajadon/Groundwater-Madhya-Pradesh)

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Note:** This system is for educational and research purposes. For official groundwater data and advisories, consult the Central Ground Water Board (CGWB) and Madhya Pradesh Water Resources Department.
