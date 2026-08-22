# Groundwater Level Forecasting System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 20+](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)

**AI-powered groundwater level prediction system for Madhya Pradesh, India**

Forecasts groundwater levels 12 months ahead using Physics-Guided Neural Networks (PGNN-LSTM) trained on 1,082 monitoring wells with 7,450 historical readings (2015-2024).

![System Overview](https://via.placeholder.com/800x400/1e40af/ffffff?text=Interactive+Groundwater+Forecast+Map)

---

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Clone and start
git clone https://github.com/yourusername/groundwater-app.git
cd groundwater-app/infra
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

That's it! The system will be ready in 30-60 seconds.

### Manual Setup

See [SETUP.md](SETUP.md) for detailed instructions on running without Docker.

---

## ✨ Features

### 🗺️ **Interactive Map**
- 1,082 monitoring wells across Madhya Pradesh
- Color-coded risk indicators (Critical/Watch/Stable)
- Click any well for detailed 12-month forecast
- Toggle between trend view and geology view

### 📈 **12-Month Forecasts**
- PGNN-LSTM machine learning model
- 99.4% coverage (1,075 wells)
- Confidence intervals (95% CI)
- Monthly predictions with uncertainty bounds

### 📊 **Risk Classification**
```
🔴 Critical: > 4m decline  (81 wells,  7.5%)
🟡 Watch:    2-4m decline  (177 wells, 16.4%)
🟢 Stable:   < 2m change   (803 wells, 74.7%)
```

### 📄 **Report Generation**
- **PDF Reports**: Well-specific or district summaries
- **CSV Exports**: Bulk data for analysis
- CGWB-compliant format for official use

### 🎯 **Custom Location Predictor**
- Predict groundwater for any location in Madhya Pradesh
- Spatial interpolation from nearest wells
- Useful for planning new monitoring stations

---

## 📸 Screenshots

### Main Map View
Interactive map showing all monitoring wells with risk-based color coding.

### Forecast Chart
12-month prediction with tight zoom to show 1-3m variations clearly.

### Well Detail Page
Complete well information, historical trends, and forecast with recommendations.

---

## 🏗️ Architecture

```
Frontend (Next.js/React)  →  Backend (FastAPI)  →  PostgreSQL + PostGIS
                                    ↓
                              ML Model (PyTorch)
                              PGNN-LSTM 1,082 nodes
```

**Tech Stack:**
- **Frontend**: Next.js 14, TypeScript, Leaflet, Recharts
- **Backend**: FastAPI, Python 3.11, SQLAlchemy
- **Database**: PostgreSQL 16 + PostGIS
- **ML**: PyTorch, PGNN-LSTM architecture
- **Deployment**: Docker Compose

---

## 📊 Model Performance

- **Training Data**: 247,328 sequences from 1,082 wells
- **Validation Loss**: 0.024074 (MSE)
- **Coverage**: 99.4% of wells with sufficient data
- **Inference Time**: < 100ms per well
- **Training Time**: 62.7 minutes (single run)

---

## 📖 Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup and configuration guide
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Comprehensive system documentation
- **[docs/API_CONTRACT.md](docs/API_CONTRACT.md)** - API reference
- **Backend API Docs**: http://localhost:8000/docs (after starting services)

---

## 🔧 Configuration

### Environment Variables

```bash
# Backend (.env or docker-compose.yml)
DATABASE_URL=postgresql://gwuser:changeme@db:5432/groundwater
MODEL_ARTIFACT_DIR=/app/ml/artifacts

# Frontend (.env.local)
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### Custom Ports

Edit `infra/docker-compose.yml`:
```yaml
frontend:
  ports:
    - "3001:3000"  # Change 3001 to your desired port
backend:
  ports:
    - "8001:8000"  # Change 8001 to your desired port
```

---

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# List wells
curl http://localhost:8000/api/v1/wells | jq

# Get forecast
curl http://localhost:8000/api/v1/forecast/well/BPL050-OW | jq

# Test database
docker-compose exec db psql -U gwuser -d groundwater -c "SELECT COUNT(*) FROM wells;"
```

---

## 🔄 Updating

### Update Code
```bash
git pull origin main
cd infra
docker-compose down
docker-compose build
docker-compose up -d
```

### Update ML Model
```bash
# After training new model
cp /path/to/new/model/* ml/artifacts/
docker-compose restart backend
```

### Update Database
```bash
# Backup first
docker-compose exec db pg_dump -U gwuser groundwater > backup.sql

# Load new data
cd etl
python load_to_postgres.py
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 API Examples

### Get Well Forecast
```bash
GET /api/v1/forecast/well/{well_id}
```

Response:
```json
{
  "well_id": "BPL050-OW",
  "matched_existing_well": true,
  "aquifer_zone": "Basalt",
  "forecast": [
    {
      "month_index": 1,
      "head_msl_m": 469.54,
      "lower_m": 468.34,
      "upper_m": 470.74
    }
  ],
  "trend_label": "Stable",
  "recommendation": "Water levels stable (1.26m change). Continue monitoring.",
  "model_version": "pgnn_lstm_v1"
}
```

### Generate PDF Report
```bash
POST /api/v1/exports/generate
Content-Type: application/json

{
  "well_ids": ["BPL050-OW"],
  "format": "pdf"
}
```

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

## 📦 Project Structure

```
groundwater-app/
├── frontend/          # Next.js React application
├── backend/           # FastAPI Python backend
├── ml/                # Machine learning (training & inference)
├── etl/               # Data extraction and loading scripts
├── data/              # CSV data files (wells, readings, rainfall)
├── infra/             # Docker Compose configuration
├── docs/              # Documentation
└── GW_Data/           # Original MS Access databases
```

---

## 🔐 Security Notes

**⚠️ This is a development setup. For production:**

- [ ] Enable authentication (JWT, OAuth)
- [ ] Restrict CORS to specific domains
- [ ] Use environment-specific secrets management
- [ ] Enable HTTPS/TLS
- [ ] Add rate limiting
- [ ] Implement audit logging
- [ ] Regular security audits

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Central Ground Water Board (CGWB)** for monitoring data
- **Madhya Pradesh Water Resources Department**
- Open-source community for excellent tools and libraries

---

## 📞 Support

- **Documentation**: See [SETUP.md](SETUP.md) and [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/groundwater-app/issues)
- **API Docs**: http://localhost:8000/docs

---

## 📊 System Status

```
✅ Model: PGNN-LSTM v1.0
✅ Wells: 1,082 total (1,075 with forecasts)
✅ Coverage: 99.4%
✅ Readings: 7,450
✅ Date Range: 2015-2024
✅ Validation Loss: 0.024074
```

---

**Built with ❤️ for sustainable groundwater management in Madhya Pradesh**

*For detailed system documentation, see [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)*
