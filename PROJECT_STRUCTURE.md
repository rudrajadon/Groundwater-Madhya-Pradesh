# MP Groundwater Monitor - Project Structure

## Overview
This document provides a complete overview of the project structure, components, and how they work together.

---

## 📁 Directory Structure

```
groundwater-app/
├── frontend/                    # Next.js frontend application
│   ├── components/             # React components
│   │   ├── Map.tsx            # Interactive Leaflet map with well markers
│   │   ├── StressMap.tsx      # District-level stress visualization
│   │   ├── ForecastChart.tsx  # 12-month forecast chart with confidence intervals
│   │   ├── LocationPredictor.tsx  # Custom GPS prediction modal
│   │   ├── ExportModal.tsx    # PDF/CSV export interface
│   │   ├── DistrictList.tsx   # District dropdown selector
│   │   ├── SettingsMenu.tsx   # Dark mode & navigation menu
│   │   └── AgreementModal.tsx # Terms & system info modal
│   ├── pages/
│   │   ├── index.tsx          # Main dashboard page
│   │   ├── about.tsx          # About page with project details
│   │   └── _app.tsx           # Next.js app wrapper
│   ├── lib/
│   │   └── api.ts             # API client for backend communication
│   ├── styles/
│   │   └── globals.css        # Global styles
│   └── public/
│       └── iiti.png           # IIT Indore logo
│
├── backend/                    # FastAPI backend application
│   └── app/
│       ├── main.py            # FastAPI app initialization
│       ├── routers/           # API route handlers
│       │   ├── forecast.py    # Well forecast endpoints
│       │   ├── exports.py     # Report generation (PDF/CSV)
│       │   ├── stress_map.py  # District stress analysis
│       │   └── wells.py       # Well metadata endpoints
│       ├── services/          # Business logic
│       │   ├── ml_inference.py      # ML model inference
│       │   ├── report_generator.py  # Report generation logic
│       │   ├── recommendation.py    # Trend classification
│       │   └── graph.py            # Dynamic graph construction
│       └── db/
│           └── database.py    # PostgreSQL connection
│
├── ml/                         # Machine learning models & training
│   ├── model.py               # PGNN-LSTM model definition
│   ├── preprocessing.py       # Data preprocessing & graph construction
│   ├── evaluate.py            # Model evaluation metrics
│   ├── train.py               # Model training script
│   └── weights/
│       └── pgnn_lstm_v3.pth   # Trained model weights
│
├── etl/                        # Data extraction, transformation, loading
│   ├── ingest_wells.py        # Load well metadata from MDB files
│   ├── ingest_water_levels.py # Load historical water level data
│   ├── classify_geology_type.py # Geology classification
│   └── fix_data_quality.py    # Data cleaning & validation
│
├── GW_Data/                    # Raw data files
│   ├── Water Level/           # .mdb files with water level measurements
│   └── Water Quality/         # .mdb files with quality parameters
│
├── 23/                         # Shapefiles for district boundaries
│   └── MP_DISTRICT_BDY.shp    # Madhya Pradesh district polygons
│
├── infra/                      # Infrastructure & deployment
│   └── docker-compose.yml     # Docker services configuration
│
├── docs/                       # Documentation
│   ├── FAQ.md                 # Frequently Asked Questions
│   ├── PROJECT_STRUCTURE.md   # This file
│   ├── README.md              # Project overview
│   └── SETUP.md               # Setup instructions
│
└── PGNN_LSTM_Final_ReviewerCorrected (5).ipynb  # Original research notebook

```

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│                     (Next.js Frontend)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Dashboard  │  │  Stress Map  │  │  Agreement Modal │  │
│  │    Page     │  │     View     │  │                  │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                           │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │   Routers    │  │   Services    │  │   ML Inference  │ │
│  │              │──│               │──│                 │ │
│  │ • Forecast   │  │ • Graph       │  │ • PGNN-LSTM    │ │
│  │ • Exports    │  │ • Reports     │  │ • Predictions  │ │
│  │ • StressMap  │  │ • Trends      │  │                 │ │
│  └──────────────┘  └───────────────┘  └─────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ SQL Queries
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   POSTGRESQL + POSTGIS                       │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │    Wells     │  │ Water Levels  │  │   Forecasts     │ │
│  │   Metadata   │  │   (Historical)│  │   (Cached)      │ │
│  └──────────────┘  └───────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### 1. **Initial Data Loading (ETL)**
```
Raw MDB Files (CGWB) 
    ↓
etl/ingest_wells.py (Well metadata)
    ↓
etl/ingest_water_levels.py (Historical measurements)
    ↓
etl/classify_geology_type.py (Geology classification)
    ↓
PostgreSQL Database
```

### 2. **User Request Flow**
```
User clicks well on map
    ↓
Frontend: API call to /forecast/{well_id}
    ↓
Backend Router: forecast.py
    ↓
Service: ml_inference.py
    ↓
Load historical data from DB
    ↓
Build graph structure (PGNN)
    ↓
Run PGNN-LSTM model
    ↓
Generate 12-month forecast
    ↓
Classify trend (Critical/Watch/Stable)
    ↓
Return JSON response
    ↓
Frontend: Display charts & details
```

### 3. **Export Report Flow**
```
User clicks "Export Report"
    ↓
Frontend: POST to /exports/generate
    ↓
Backend: report_generator.py
    ↓
Fetch well data & forecast
    ↓
Generate PDF using reportlab / CSV using pandas
    ↓
Return file download
    ↓
User saves file
```

---

## 🧩 Key Components

### Frontend Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **Map.tsx** | Interactive well visualization | Leaflet map, zoom-responsive markers, click handlers |
| **StressMap.tsx** | District stress overlay | Heat maps, color-coded risk levels, district selection |
| **ForecastChart.tsx** | Forecast visualization | Recharts line chart, confidence intervals, responsive |
| **LocationPredictor.tsx** | Custom GPS predictions | Lat/lng input, spatial interpolation |
| **ExportModal.tsx** | Report generation | PDF/CSV selection, loading states |
| **DistrictList.tsx** | District selector | Dropdown with stress indicators |
| **SettingsMenu.tsx** | App settings | Dark/light mode, navigation |
| **AgreementModal.tsx** | Terms & info | Model metrics, limitations, IIT Indore branding |

### Backend Services

| Service | Purpose | Key Functions |
|---------|---------|---------------|
| **ml_inference.py** | ML predictions | `forecast_well()`, load model, run inference |
| **graph.py** | Dynamic graph construction | `build_graph()`, edge weighting, spatial relationships |
| **report_generator.py** | Report creation | `generate_pdf()`, `generate_csv()` |
| **recommendation.py** | Trend classification | `classify_trend()`, stress assessment |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/forecast/{well_id}` | GET | Get 12-month forecast for a well |
| `/forecast/location` | POST | Predict at custom GPS coordinates |
| `/wells` | GET | List all monitoring wells |
| `/wells/{well_id}` | GET | Get well metadata |
| `/wells/{well_id}/history` | GET | Get historical water levels |
| `/exports/generate` | POST | Generate PDF/CSV report |
| `/stress-map/districts` | GET | Get district stress analysis |
| `/stress-map/district/{name}` | GET | Get specific district details |

---

## 🔧 Technology Stack

### Frontend
- **Framework:** Next.js 14 (React 18)
- **Language:** TypeScript
- **Mapping:** Leaflet.js
- **Charts:** Recharts
- **Styling:** Inline styles (CSS-in-JS)
- **State Management:** React hooks (useState, useEffect)

### Backend
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL 15 + PostGIS
- **ML Framework:** PyTorch
- **PDF Generation:** reportlab
- **Data Processing:** pandas, numpy
- **ORM:** SQLAlchemy

### Machine Learning
- **Model:** PGNN-LSTM (Position-aware Graph Neural Network + LSTM)
- **Framework:** PyTorch
- **Graph Processing:** Custom graph convolution layers
- **Training:** Supervised learning on historical sequences
- **Performance:** RMSE 3.40m, R² 0.65

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Services:**
  - Frontend: Node.js container (port 3000)
  - Backend: Python container (port 8000)
  - Database: PostgreSQL container (port 5432)

---

## 📊 Database Schema

### Tables

**wells**
- `well_id` (PK): Unique well identifier
- `latitude`, `longitude`: GPS coordinates
- `district`: District name
- `block`: Block/Mandal name
- `geology_type`: Basalt/Granite/Vindhyan
- `aquifer_type`: Weathered/Fractured/Massive
- `depth_bgl_m`: Depth below ground level

**water_levels**
- `id` (PK): Auto-increment ID
- `well_id` (FK): Reference to wells table
- `date`: Measurement date
- `depth_bgl_m`: Water level depth below ground
- `head_msl_m`: Water level head above MSL

**forecasts** (cached predictions)
- `well_id` (PK): Well identifier
- `forecast_data`: JSON array of predictions
- `generated_at`: Timestamp of forecast generation
- `trend_label`: Critical/Watch/Stable

---

## 🚀 Deployment

### Development Environment
```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Database
docker-compose up db
```

### Production Deployment
```bash
# Full stack with Docker Compose
docker-compose up -d

# Services start:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - Database: postgresql://localhost:5432
```

---

## 🔐 Security Considerations

1. **Agreement Modal:** Users must accept terms before using the system
2. **Data Validation:** Input sanitization on all API endpoints
3. **CORS:** Configured for frontend-backend communication
4. **No Authentication:** Currently open system (add auth for production)
5. **Data Privacy:** No personal data collected; only well IDs and predictions

---

## 📈 Performance Optimization

1. **Forecast Caching:** Generated forecasts cached in database
2. **Database Indexing:** Well IDs and dates indexed for fast queries
3. **Lazy Loading:** Map markers loaded progressively
4. **Code Splitting:** Next.js automatic code splitting
5. **Connection Pooling:** PostgreSQL connection pool in backend

---

## 🧪 Testing

### Model Evaluation
```bash
python ml/evaluate.py
# Outputs: Per-well RMSE, MAE, R², NSE metrics
```

### API Testing
- Use FastAPI's built-in `/docs` Swagger UI
- Access: http://localhost:8000/docs

### Frontend Testing
- Manual testing via browser
- Use React DevTools for component debugging

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Project overview and quick start |
| **SETUP.md** | Detailed setup instructions |
| **FAQ.md** | 10 common questions with detailed answers |
| **PROJECT_STRUCTURE.md** | This file - complete architecture |
| **CHANGES_SUMMARY.md** | Development changelog |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -m "Add new feature"`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

---

## 📞 Contact & Support

- **Developer:** Rudra Pratap Singh Jadon
- **Guidance:** Dr. Manish Kumar Goyal (IIT Indore), Deepak Mishra (PhD Scholar, IIT Indore)
- **Institution:** Indian Institute of Technology, Indore
- **Data Source:** Central Ground Water Board (CGWB)

---

*Last Updated: January 2025*
*Version: 1.0*
