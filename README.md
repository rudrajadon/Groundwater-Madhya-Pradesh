# 💧 Madhya Pradesh Groundwater Forecast System

A full-stack web application for monitoring and forecasting groundwater levels in Madhya Pradesh, India. Uses machine learning (PGNN-LSTM) to predict water levels 12 months ahead and provides interactive visualizations for policymakers and water resource managers.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-14.2-black.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-green.svg)

## 🌟 Features

### 📊 Interactive Mapping
- **Well Map**: Visualize 1,196+ monitoring wells across Madhya Pradesh
- **Stress Map**: District-level groundwater stress assessment with color-coded indicators
- **Custom Location Predictor**: Get forecasts for any GPS coordinates in the state

### 📈 Forecasting & Analytics
- **12-month ahead predictions** using Physics-Guided Neural Networks (PGNN-LSTM)
- **Historical data visualization** with trend analysis
- **Well classification**: Critical, Watch, and Stable status based on decline rates
- **District summaries**: Aggregated statistics for administrative planning

### 📄 Report Generation
- **PDF Reports**: CGWB-compliant detailed reports with charts and recommendations
- **CSV Export**: Raw forecast data for single wells
- **District Summary Reports**: Multi-well summaries with statistics
- Auto-generated reports with official headers and visualizations

### 🎯 Key Capabilities
- Real-time forecast visualization with interactive charts
- Responsive UI optimized for desktop and tablet
- Clean, professional design following Material Design principles
- RESTful API for integration with other systems

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  • React 18 + TypeScript                                     │
│  • Leaflet maps with custom overlays                         │
│  • Recharts for data visualization                           │
│  • Server-side rendering for SEO                             │
└────────────────┬────────────────────────────────────────────┘
                 │ REST API
┌────────────────▼────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  • Python 3.11 with async/await                              │
│  • PGNN-LSTM model inference                                 │
│  • PDF/CSV generation with ReportLab                         │
│  • Spatial queries with PostGIS                              │
└────────────────┬────────────────────────────────────────────┘
                 │ SQL
┌────────────────▼────────────────────────────────────────────┐
│                   Database (PostgreSQL + PostGIS)            │
│  • 1,196 wells with coordinates                              │
│  • Historical water level data (2000-2024)                   │
│  • Lithology and aquifer characteristics                     │
│  • Spatial indexing for fast queries                         │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose** (recommended)
- OR Python 3.11+, Node.js 20+, PostgreSQL 16 with PostGIS

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/groundwater-app.git
cd groundwater-app

# Start all services
cd infra
docker-compose up -d

# Wait for services to be healthy (about 30 seconds)
docker-compose ps

# Access the application
open http://localhost:3000
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Manual Setup

See [RUNBOOK.md](docs/RUNBOOK.md) for detailed manual installation instructions.

## 📁 Project Structure

```
groundwater-app/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application entry
│   │   ├── routers/        # API endpoints
│   │   │   ├── wells.py    # Well data endpoints
│   │   │   ├── forecast.py # Forecast endpoints
│   │   │   ├── zones.py    # District/zone endpoints
│   │   │   └── exports.py  # PDF/CSV generation
│   │   ├── services/       # Business logic
│   │   │   ├── graph.py    # ML model service
│   │   │   └── recommendation.py
│   │   ├── db.py          # Database connection
│   │   └── schemas.py     # Pydantic models
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/               # Next.js frontend
│   ├── components/        # React components
│   │   ├── Map.tsx       # Well map with markers
│   │   ├── StressMap.tsx # District stress map
│   │   ├── ForecastChart.tsx
│   │   ├── ExportModal.tsx
│   │   └── LocationPredictor.tsx
│   ├── pages/
│   │   ├── index.tsx     # Main application page
│   │   └── _app.tsx      # App wrapper
│   ├── lib/
│   │   ├── api.ts        # API client
│   │   └── location-api.ts
│   ├── package.json
│   └── Dockerfile
│
├── etl/                   # Data pipeline
│   ├── export_mdb.sh     # MS Access database export
│   ├── parse_coordinates.py
│   ├── fetch_rainfall_openmeteo.py
│   ├── load_to_postgres.py
│   └── schema.sql        # Database schema
│
├── ml/                    # Machine learning
│   └── artifacts/        # Trained PGNN-LSTM model
│
├── data/                 # Processed CSV data
│   ├── wells.csv
│   ├── water_levels.csv
│   └── litho.csv
│
├── GW_Data/              # Original MS Access databases
│   ├── Water Level/
│   └── Water Quality/
│
├── docs/                 # Documentation
│   ├── API_CONTRACT.md
│   ├── PROJECT_PLAN.md
│   └── RUNBOOK.md
│
├── infra/                # Infrastructure
│   └── docker-compose.yml
│
├── .gitignore
└── README.md
```

## 🔌 API Documentation

### Key Endpoints

#### Wells
```http
GET /api/v1/wells
GET /api/v1/wells/{well_id}
GET /api/v1/wells/{well_id}/history
```

#### Forecasts
```http
GET /api/v1/forecast/well/{well_id}
POST /api/v1/forecast/location
```

#### Districts
```http
GET /api/v1/zones
GET /api/v1/zones/{zone_name}/wells
```

#### Exports
```http
POST /api/v1/exports/generate
{
  "format": "pdf",
  "report_type": "well",
  "well_ids": ["SIND-PTW 38-PZ"]
}
```

Full API documentation: http://localhost:8000/docs

## 🗄️ Database Schema

The PostgreSQL database contains:

- **wells** (1,196 records): Well metadata, coordinates, district, geology
- **water_level_readings** (~50,000 records): Historical measurements
- **lithology**: Aquifer characteristics and stratigraphy
- **rainfall**: Historical precipitation data from Open-Meteo

See [etl/schema.sql](etl/schema.sql) for complete schema.

## 🧪 Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
DATABASE_URL="postgresql://gwuser:changeme@localhost:5432/groundwater" \
MODEL_ARTIFACT_DIR="../ml/artifacts" \
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev

# Build for production
npm run build
npm start
```

## 📊 Data Sources

- **Water Level Data**: Central Ground Water Board (CGWB), India
- **Well Coordinates**: GPS surveys and government records
- **Rainfall Data**: Open-Meteo API (ERA5 reanalysis)
- **Lithology**: Geological Survey of India
- **Administrative Boundaries**: Survey of India

## 🤖 Machine Learning Model

The forecasting system uses a **Physics-Guided Neural Network (PGNN)** combined with **LSTM** architecture:

- **Input Features**: Historical water levels, rainfall, season, well characteristics
- **Architecture**: Graph Neural Network + LSTM layers
- **Training**: 1,196 wells with 20+ years of data
- **Performance**: R² > 0.85 on test set
- **Inference Time**: <100ms per well

Model artifacts are stored in `ml/artifacts/`.

## 🐳 Docker Services

The application runs three containerized services:

1. **Database (PostgreSQL + PostGIS)**
   - Port: 5432
   - Health checks enabled
   - Persistent volume for data

2. **Backend (FastAPI)**
   - Port: 8000
   - Depends on database
   - Auto-reload in development

3. **Frontend (Next.js)**
   - Port: 3000
   - Depends on backend
   - Server-side rendering enabled

## 🔧 Configuration

### Environment Variables

Create `.env` files or set environment variables:

**Backend:**
```bash
DATABASE_URL=postgresql://gwuser:changeme@db:5432/groundwater
MODEL_ARTIFACT_DIR=/app/ml/artifacts
```

**Frontend:**
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## 📝 Usage Examples

### Generate PDF Report
1. Click on any well marker on the map
2. Click "Generate Report" button
3. Select "Well Forecast Report" and PDF format
4. Click "Generate Report"

### Custom Location Forecast
1. Click "Custom Location Predictor" button
2. Enter latitude/longitude or use GPS
3. Adjust number of nearest wells (k-neighbors)
4. Click "Generate Forecast"

### District Summary
1. Click on any well in a district
2. Click "Generate Report"
3. Select "District Summary Report"
4. Scope automatically switches to district
5. Generate PDF with all wells in that district

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Rudra Jadon** - Initial work

## 🙏 Acknowledgments

- Central Ground Water Board (CGWB) for providing water level data
- Open-Meteo for rainfall data API
- PostgreSQL and PostGIS communities
- React, Next.js, and FastAPI communities

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Note**: This is a demonstration project for groundwater monitoring. For production deployment, ensure proper security measures, authentication, and data validation are implemented.
