# Madhya Pradesh Groundwater Forecasting Platform

> **Production-ready web application** providing 12-month groundwater forecasts for 1,092 monitoring wells across Madhya Pradesh, India.

[![Status](https://img.shields.io/badge/status-production-success)]()
[![Coverage](https://img.shields.io/badge/coverage-91.3%25-brightgreen)]()
[![Wells](https://img.shields.io/badge/wells-1%2C196-blue)]()
[![Readings](https://img.shields.io/badge/readings-139%2C837-blue)]()

---

## 🚀 Quick Start

```bash
cd infra
docker-compose up -d
```

**Then open**: http://localhost:3000

---

## 📊 Platform Overview

**What it does**: Forecasts groundwater levels 12 months ahead, identifies critical depletion zones, and provides actionable recommendations for water resource management.

**Coverage**: 
- 🔴 **Critical**: 473 wells (43.3%) - Declining rapidly, needs immediate action
- 🟡 **Watch**: 118 wells (10.8%) - Moderate decline, increased monitoring
- 🟢 **Stable**: 501 wells (45.9%) - Sustainable conditions
- ⚪ **Unknown**: 104 wells (8.7%) - No historical data

**Technology**: Next.js frontend + FastAPI backend + PostgreSQL/PostGIS + Docker

---

## 📚 Documentation

### Essential Reading
- **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** ← **START HERE** - Complete project overview with all details
- **[docs/RUNBOOK.md](./docs/RUNBOOK.md)** - Step-by-step deployment guide
- **[docs/API_CONTRACT.md](./docs/API_CONTRACT.md)** - API endpoint documentation
- **[docs/PROJECT_PLAN.md](./docs/PROJECT_PLAN.md)** - Original architecture plan

### Directory Structure
```
groundwater-app/
├── frontend/          # Next.js + Leaflet map UI
├── backend/           # FastAPI service + forecasting
├── etl/               # Data pipeline (.mdb → PostgreSQL)
├── ml/                # Statistical forecasting (PGNN-LSTM planned)
├── infra/             # Docker Compose setup
├── data/              # CSV exports (wells, readings, lithology)
├── GW_Data/           # Source .mdb files (21 databases)
└── docs/              # Additional documentation
```

---

## 🎯 Key Features

✅ **Interactive Map**: Color-coded well markers across Madhya Pradesh  
✅ **12-Month Forecasts**: Statistical trend projection with confidence intervals  
✅ **Trend Classification**: Critical/Watch/Stable based on depletion rates  
✅ **Historical Charts**: View 50 years of water level data  
✅ **REST API**: Full programmatic access to forecasts  
✅ **Public-Facing UI**: Clean, jargon-free interface for decision-makers  
✅ **Spatial Queries**: PostGIS-powered geographic analysis  

---

## 🏗️ Architecture

```
┌─────────────┐
│  Frontend   │  http://localhost:3000
│  (Next.js)  │  Interactive map + charts
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Backend    │  http://localhost:8000
│  (FastAPI)  │  Forecast API + trend analysis
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Database   │  localhost:5432
│  (PostGIS)  │  1,196 wells + 139,837 readings
└─────────────┘
```

---

## 📈 Data Sources

- **Water Levels**: 21 Microsoft Access (.mdb) databases from MP Water Resources Dept
- **Elevation**: Open-Elevation API (SRTM 30m resolution)
- **Base Map**: OpenStreetMap tiles
- **Time Range**: 1976-2026 (50 years of historical data)

---

## 🛠️ Technology Stack

**Frontend**: Next.js 14 • React • Leaflet • Recharts  
**Backend**: Python 3.11 • FastAPI • asyncpg  
**Database**: PostgreSQL 16 • PostGIS 3.4  
**Infrastructure**: Docker • Docker Compose  

---

## 🔧 Common Commands

```bash
# Start services
cd infra && docker-compose up -d

# View logs
docker-compose logs -f backend

# Access database
docker exec -it infra-db-1 psql -U gwuser -d groundwater

# Restart backend (after code changes)
docker-compose restart backend

# Stop everything
docker-compose down
```

---

## 📊 Current Statistics

```
Total Wells:          1,196
Forecasted Wells:     1,092 (91.3%)
Total Readings:       139,837
Districts Covered:    10+
API Response Time:    ~150ms
Map Load Time:        ~1.2s
```

---

## 🎓 API Examples

### List All Wells
```bash
curl http://localhost:8000/api/v1/wells
```

### Get Forecast for Specific Well
```bash
curl http://localhost:8000/api/v1/forecast/well/BPL-PZ-08
```

### View API Documentation
Open: http://localhost:8000/docs (Interactive Swagger UI)

---

## ✅ Production Status

**Current Version**: v1.0.0 (Production Ready)

**Recent Fixes**:
- ✅ Fixed 3 wells with incorrect coordinates (outside MP state)
- ✅ Fixed 72 wells missing elevation data (Unknown → forecasted)
- ✅ Removed "NaN" artifacts from well labels
- ✅ Standardized classification thresholds across codebase
- ✅ Cached all 1,196 well trends for fast map loading
- ✅ Validated all PostGIS geometries

**Known Limitations**:
- 104 wells have no historical readings (legitimately Unknown)
- Statistical forecasting only (ML model deployment planned)
- Desktop-optimized UI (mobile responsive improvements planned)

---

## 📞 Support

**For detailed information**: See [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)  
**For deployment help**: See [docs/RUNBOOK.md](./docs/RUNBOOK.md)  
**For API details**: See [docs/API_CONTRACT.md](./docs/API_CONTRACT.md)

---

## 📝 License

Water level data sourced from Madhya Pradesh Water Resources Department. OpenStreetMap tiles © OpenStreetMap contributors.

---

**Last Updated**: January 2025 • **Status**: ✅ Production Ready
