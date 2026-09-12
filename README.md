# MP Groundwater Monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 20+](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000.svg)](https://nextjs.org/)

**AI-Powered Groundwater Level Forecasting System for Madhya Pradesh, India**

An interactive web application that forecasts groundwater levels 12 months ahead using hybrid PGNN-LSTM (Position-aware Graph Neural Network + LSTM) machine learning architecture. Trained on 1,082+ monitoring wells with comprehensive geological and aquifer metadata.

**🎓 Developed at IIT Indore**  
*Under the guidance of Dr. Manish Kumar Goyal (Professor, IIT Indore) and Deepak Mishra (PhD Scholar, IIT Indore)*

---

## � Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [System Overview](#-system-overview)
- [Model Performance](#-model-performance)
- [Documentation](#-documentation)
- [Usage Guide](#-usage-guide)
- [API Examples](#-api-examples)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)

---

## �🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/rudrajadon/Groundwater-Madhya-Pradesh.git
cd Groundwater-Madhya-Pradesh

# Start all services
cd infra
docker-compose up -d

# Access the application
# 🌐 Frontend: http://localhost:3000
# 🔧 Backend API: http://localhost:8000/docs
# 🗄️ Database: postgresql://localhost:5432
```

The system will be ready in 30-60 seconds!

### Option 2: Manual Setup

```bash
# 1. Start PostgreSQL database
cd infra
docker-compose up -d db

# 2. Start backend
cd ../backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Start frontend
cd ../frontend
npm install
npm run dev
```

For detailed setup instructions, see [SETUP.md](SETUP.md).

---

## ✨ Features

### 🗺️ **Interactive Visualization**
- **1,082+ monitoring wells** across 10+ districts in Madhya Pradesh
- **Dual map views:**
  - **Wells Map**: Individual well locations with zoom-responsive markers
  - **Stress Map**: District-level risk assessment with color-coded overlays
- **Real-time interaction**: Click any well to see detailed forecasts, history, and trends
- **District filtering**: Select specific districts to focus analysis
- **Dark mode support**: Toggle between light and dark themes

### 📈 **AI-Powered Forecasts**
- **12-month predictions** with monthly granularity
- **Hybrid PGNN-LSTM model**:
  - Spatial dependencies via Graph Neural Networks
  - Temporal patterns via LSTM networks
- **95% confidence intervals** for uncertainty quantification
- **Trend classification**: Critical / Watch / Stable
- **Model metrics**: RMSE 3.40m, R² 0.65, MAE 2.8m

### 🎯 **Custom Location Predictor**
- Predict groundwater at **any GPS coordinates** in Madhya Pradesh
- Spatial interpolation from nearest monitoring wells
- Useful for planning new wells or site assessments
- Transparent uncertainty indicators

### 📊 **Comprehensive Analysis**
- **Historical water levels**: Multi-year trend visualization
- **Geological context**: Basalt, Granite, Vindhyan formations
- **Aquifer characteristics**: Weathered, Fractured, Massive zones
- **District stress analysis**: Percentage of Critical/Watch/Stable wells
- **Seasonal patterns**: Monsoon recharge and dry season depletion

### 📄 **Export & Reporting**
- **PDF Reports**: Well-specific summaries with charts and recommendations
- **CSV Exports**: Bulk data for external analysis
- **Print-ready format**: Suitable for official documentation
- **CGWB-compliant**: Follows Central Ground Water Board standards

### 🔐 **User Experience**
- **Agreement modal**: Terms, system info, and model limitations upfront
- **Responsive design**: Works on desktop, tablet, and mobile
- **Settings menu**: Easy navigation and theme switching
- **Fast loading**: Optimized performance with caching

---

## 📸 Screenshots

### Main Map View
Interactive map showing all monitoring wells with risk-based color coding.

### Forecast Chart
12-month prediction with tight zoom to show 1-3m variations clearly.

### Well Detail Page
Complete well information, historical trends, and forecast with recommendations.

---

## 🏗️ System Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER BROWSER (React)                     │
│  Interactive Map | Forecast Charts | District Analysis      │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST API (HTTP/JSON)
┌───────────────────────────▼─────────────────────────────────┐
│                   FASTAPI BACKEND (Python)                   │
│  Routers | Services | ML Inference | Report Generation      │
└───────────────────────────┬─────────────────────────────────┘
                            │ SQL Queries
┌───────────────────────────▼─────────────────────────────────┐
│              POSTGRESQL + POSTGIS DATABASE                   │
│  Wells Metadata | Historical Levels | Cached Forecasts      │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ Model Inference
┌───────────────────────────┴─────────────────────────────────┐
│                  PGNN-LSTM ML MODEL (PyTorch)                │
│  1,082-node graph | LSTM temporal encoder | Prediction head  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Next.js 14, TypeScript, React 18 | User interface |
| **Mapping** | Leaflet.js | Interactive maps |
| **Charts** | Recharts | Data visualization |
| **Backend** | FastAPI, Python 3.11 | API server |
| **Database** | PostgreSQL 15 + PostGIS | Spatial data storage |
| **ML Framework** | PyTorch | Model training & inference |
| **Deployment** | Docker Compose | Container orchestration |

### Data Flow

1. **User clicks well** → Frontend sends request to `/forecast/{well_id}`
2. **Backend** → Fetches historical data from PostgreSQL
3. **ML Service** → Builds spatial graph, runs PGNN-LSTM model
4. **Backend** → Returns 12-month forecast with confidence intervals
5. **Frontend** → Renders interactive chart and recommendations

For detailed architecture, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

---

## 📊 Model Performance

### Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **RMSE** | 3.40 m | Average prediction error (meters) |
| **MAE** | 2.8 m | Median absolute error |
| **R² Score** | 0.65 | Model explains 65% of variance |
| **Coverage** | 1,082+ wells | All wells in Madhya Pradesh network |

### Model Architecture: PGNN-LSTM

**Position-aware Graph Neural Network + Long Short-Term Memory**

1. **Spatial Component (PGNN)**
   - Models wells as nodes in a graph network
   - Edges weighted by distance, geology, aquifer type
   - Captures spatial dependencies between neighboring wells

2. **Temporal Component (LSTM)**
   - Processes historical time-series (up to 5+ years)
   - Learns seasonal patterns (monsoon, dry season)
   - Captures long-term trends (decline, recovery, stable)

3. **Training**
   - 52 high-quality monitoring wells
   - Multi-year historical sequences (2015-2024)
   - Validated on hold-out test set

**Innovation**: Unlike traditional time-series models, PGNN-LSTM explicitly models spatial correlation between wells, improving predictions in data-sparse regions.

### Performance Context

- R² of 0.65 is **good to very good** for groundwater forecasting
- Groundwater is highly complex with many unmodeled factors (rainfall, pumping, recharge)
- Predictions most reliable for **1-6 months ahead**; confidence decreases toward 12 months
- Higher accuracy in weathered/massive basalt zones (R² ~0.65) vs fractured zones (R² ~0.50)

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[FAQ.md](FAQ.md)** | 10 frequently asked questions covering usage, limitations, reliability, ML details |
| **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** | Complete system architecture, components, data flow, and tech stack |
| **[SETUP.md](SETUP.md)** | Detailed installation and configuration guide |
| **[docs/API_CONTRACT.md](docs/API_CONTRACT.md)** | API endpoint reference and examples |
| **API Docs (Swagger)** | Interactive API documentation at `http://localhost:8000/docs` |

**Quick Links:**
- 🤔 [How do I use this app?](FAQ.md#1-how-do-i-use-this-application)
- ⚠️ [What are the limitations?](FAQ.md#2-what-are-the-limitations-of-this-system)
- 📈 [How reliable are forecasts?](FAQ.md#5-how-reliable-are-the-forecasts)
- 🔧 [How does the ML model work?](FAQ.md#9-how-does-the-machine-learning-model-work)

---

## 💡 Usage Guide

### 1. **View District Overview**
- Open the app → Select a district from the dropdown
- See all wells in that district with color-coded risk indicators:
  - 🔴 **Red**: Critical (declining >0.5m/year)
  - 🟡 **Yellow**: Watch (moderate decline 0.2-0.5m/year)
  - 🟢 **Green**: Stable (<0.2m/year change)

### 2. **Analyze Individual Wells**
- Click any well marker on the map
- View:
  - Historical water levels (multi-year trends)
  - 12-month forecast with confidence intervals
  - Geology type and aquifer characteristics
  - Trend classification and recommendations

### 3. **District Stress Analysis**
- Toggle to "Stress Map" view
- See district-level risk percentages
- Identify high-risk districts for policy intervention

### 4. **Custom Location Prediction**
- Click "Custom Location" button
- Enter GPS coordinates (latitude, longitude)
- Get predicted groundwater levels based on nearest wells

### 5. **Export Reports**
- Select one or more wells
- Click "Export Report"
- Choose PDF (formatted report) or CSV (raw data)
- Use for documentation, presentations, or further analysis

### 6. **Settings**
- Click settings icon (top right)
- Toggle dark/light mode
- Navigate to About page for project details

---

## �️ Development

### Project Structure

```
groundwater-app/
├── frontend/              # Next.js frontend (TypeScript)
│   ├── components/       # React components (Map, Charts, Modals)
│   ├── pages/           # Next.js pages (index, about, well detail)
│   ├── lib/             # API client and utilities
│   └── public/          # Static assets (images, GeoJSON)
├── backend/              # FastAPI backend (Python)
│   ├── app/
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic (ML inference, reports)
│   │   └── db/          # Database connection
├── ml/                   # Machine learning
│   ├── model.py         # PGNN-LSTM model definition
│   ├── preprocessing.py # Data preparation & graph construction
│   ├── train.py         # Model training script
│   └── artifacts/       # Trained model weights
├── etl/                  # Data extraction & loading
│   └── ingest_*.py      # Scripts to load data from MDB files
├── GW_Data/              # Raw data files (.mdb from CGWB)
├── infra/                # Docker Compose configuration
└── docs/                 # Documentation

```

### Local Development

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Access: http://localhost:3000
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Access: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Database:**
```bash
cd infra
docker-compose up -d db
# Access: postgresql://gwuser:changeme@localhost:5432/groundwater
```

### Environment Variables

**Backend (.env):**
```bash
DATABASE_URL=postgresql://gwuser:changeme@localhost:5432/groundwater
MODEL_ARTIFACT_DIR=../ml/artifacts
CORS_ORIGINS=http://localhost:3000
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### Testing

**Backend Health Check:**
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

**Database Test:**
```bash
docker-compose exec db psql -U gwuser -d groundwater -c "SELECT COUNT(*) FROM wells;"
```

**Frontend Build:**
```bash
cd frontend
npm run build
npm start
```

### Code Style

- **Frontend**: ESLint + Prettier (auto-format on save)
- **Backend**: Black + isort for Python formatting
- **Commits**: Conventional Commits format (`feat:`, `fix:`, `docs:`, etc.)

### Updating ML Model

```bash
# 1. Train new model
cd ml
python train.py

# 2. Copy artifacts
cp artifacts/pgnn_lstm_best.pt ../backend/ml/artifacts/

# 3. Restart backend
docker-compose restart backend
```

---

## 🤝 Contributing

Contributions are welcome! This project is open-source and designed for collaborative improvement.

### How to Contribute

1. **Fork the repository**
   ```bash
   gh repo fork rudrajadon/Groundwater-Madhya-Pradesh
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation

4. **Commit your changes**
   ```bash
   git commit -m "feat: add your feature description"
   ```
   Use conventional commit format: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`

5. **Push and create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Then create PR on GitHub
   ```

### Areas for Contribution

- 🐛 **Bug fixes**: Report or fix issues
- ✨ **Features**: New visualizations, export formats, analysis tools
- 📊 **ML improvements**: Model architecture, training strategies, evaluation
- 📝 **Documentation**: Tutorials, use cases, translations
- 🧪 **Testing**: Unit tests, integration tests, performance tests
- 🎨 **UI/UX**: Design improvements, accessibility enhancements

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the problem, not the person
- Help newcomers get started

### Questions?

- Open a [GitHub Issue](https://github.com/rudrajadon/Groundwater-Madhya-Pradesh/issues) for bugs or feature requests
- See [FAQ.md](FAQ.md) for common questions
- Contact the research team for collaboration opportunities

---

## 📝 API Examples

### 1. Get Well Forecast

```bash
GET http://localhost:8000/api/v1/forecast/well/BPL050-OW
```

**Response:**
```json
{
  "well_id": "BPL050-OW",
  "district": "Bhopal",
  "aquifer_zone": "Basalt - Weathered",
  "geology_type": "Basalt",
  "forecast": [
    {
      "month_index": 1,
      "date": "2025-02-01",
      "head_msl_m": 469.54,
      "depth_bgl_m": 12.46,
      "lower_m": 468.34,
      "upper_m": 470.74
    },
    // ... 11 more months
  ],
  "trend_label": "Stable",
  "trend_change_m": -1.26,
  "recommendation": "Water levels stable with minimal change (-1.26m over 12 months). Continue routine monitoring.",
  "confidence": "High"
}
```

### 2. List All Wells

```bash
GET http://localhost:8000/api/v1/wells?district=Bhopal&limit=10
```

### 3. Get District Stress Analysis

```bash
GET http://localhost:8000/api/v1/stress-map/district/Bhopal
```

**Response:**
```json
{
  "district": "Bhopal",
  "total_wells": 156,
  "critical_count": 12,
  "watch_count": 28,
  "stable_count": 116,
  "critical_percent": 7.7,
  "watch_percent": 17.9,
  "stable_percent": 74.4,
  "risk_level": "Low"
}
```

### 4. Custom Location Prediction

```bash
POST http://localhost:8000/api/v1/forecast/location
Content-Type: application/json

{
  "latitude": 23.2599,
  "longitude": 77.4126
}
```

### 5. Generate PDF Report

```bash
POST http://localhost:8000/api/v1/exports/generate
Content-Type: application/json

{
  "well_ids": ["BPL050-OW", "BPL051-OW"],
  "format": "pdf",
  "include_charts": true
}
```

**Returns:** PDF file download with well details, forecasts, and charts.

For complete API documentation, visit `http://localhost:8000/docs` after starting the backend.

---

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db

# Restart specific service
docker-compose restart backend
```

### Database Connection Issues
```bash
# Verify database is healthy
docker-compose ps

# Connect manually
docker-compose exec db psql -U gwuser -d groundwater
```

### Frontend Shows Old Data
```bash
# Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)
# Or rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

See [SETUP.md](SETUP.md#troubleshooting) for more troubleshooting tips.

---

## ⚠️ Important Limitations

1. **Historical Pattern Dependency**: Model assumes continuation of past patterns; may not predict unprecedented events (extreme droughts, unusual monsoons)
2. **No Real-Time Factors**: Does not incorporate current rainfall, active pumping, or ongoing recharge activities
3. **Regional Accuracy Variation**: Performance varies by geology and data quality (R² 0.50-0.65)
4. **12-Month Horizon**: Forecasts limited to 12 months; longer predictions require different approaches
5. **Planning Tool**: Designed for long-term planning, not day-to-day operational decisions

**For full details, see [FAQ.md - Limitations](FAQ.md#2-what-are-the-limitations-of-this-system)**

---

## 🔐 Security & Production Deployment

**⚠️ Current setup is for development. For production:**

- [ ] Enable authentication (JWT tokens, OAuth)
- [ ] Restrict CORS to specific domains
- [ ] Use environment-specific secrets (not hardcoded passwords)
- [ ] Enable HTTPS/TLS with valid certificates
- [ ] Implement rate limiting and request throttling
- [ ] Add audit logging for all actions
- [ ] Set up monitoring and alerting (Prometheus, Grafana)
- [ ] Regular database backups
- [ ] Security audits and penetration testing

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

You are free to:
- ✅ Use commercially
- ✅ Modify and distribute
- ✅ Use privately
- ✅ Use for research

With the requirement to:
- 📝 Include the original license and copyright notice

---

## 🙏 Acknowledgments

- **Central Ground Water Board (CGWB)** - Monitoring data and technical support
- **Madhya Pradesh Water Resources Department** - State-level data and coordination
- **IIT Indore** - Research infrastructure and guidance
- **Open-source community** - PyTorch, FastAPI, Next.js, Leaflet, and countless other libraries

---

## 📞 Contact & Support

### For Technical Support
- **Developer**: Rudra Pratap Singh Jadon
- **GitHub Issues**: [Report bugs or request features](https://github.com/rudrajadon/Groundwater-Madhya-Pradesh/issues)

### For Research Collaboration
- **Principal Investigator**: Dr. Manish Kumar Goyal, Professor, IIT Indore
- **Co-Investigator**: Deepak Mishra, PhD Scholar, IIT Indore
- **Institution**: Indian Institute of Technology, Indore

### For Data & Policy Queries
- **Central Ground Water Board (CGWB)**: [cgwb.gov.in](http://cgwb.gov.in)
- **MP Water Resources Department**: Contact for official policy implementation

### For Academic Use
- Researchers are encouraged to use this system for studies
- Please cite: "MP Groundwater Monitor, IIT Indore, 2025"
- Contact research team for detailed methodology and data access

---

## 📊 System Status

| Metric | Value |
|--------|-------|
| **Model Version** | PGNN-LSTM v1.0 |
| **Wells** | 1,082+ monitoring wells |
| **Districts** | 10+ districts in Madhya Pradesh |
| **Date Range** | 2015-2024 (multi-year historical data) |
| **Forecast Horizon** | 12 months |
| **RMSE** | 3.40 m |
| **R² Score** | 0.65 |
| **Coverage** | Entire Madhya Pradesh groundwater network |

---

## 🔗 Quick Links

- 📖 [Comprehensive FAQ](FAQ.md) - 10 detailed questions & answers
- 🏗️ [Architecture Guide](PROJECT_STRUCTURE.md) - Complete system documentation
- 🚀 [Setup Instructions](SETUP.md) - Installation and configuration
- 🔌 [API Documentation](docs/API_CONTRACT.md) - Endpoint reference
- 🐙 [GitHub Repository](https://github.com/rudrajadon/Groundwater-Madhya-Pradesh)
- 📊 [Interactive API Docs](http://localhost:8000/docs) - Swagger UI (after starting backend)

---

**Built with ❤️ at IIT Indore for sustainable groundwater management**

*Developed by Rudra Pratap Singh Jadon under the guidance of Dr. Manish Kumar Goyal and Deepak Mishra*
