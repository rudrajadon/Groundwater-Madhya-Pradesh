# Quick Reference Guide

## 🚨 Emergency Quick Start
```bash
cd /Users/rudrajadon/Downloads/groundwater-app/infra
docker-compose up -d
# Wait 30 seconds, then open: http://localhost:3000
```

---

## 📍 Service URLs
| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Main web application |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| API Health | http://localhost:8000/health | Service health check |
| Database | localhost:5432 | PostgreSQL connection |

---

## 🗂️ Database Credentials
```
Host:     localhost
Port:     5432
Database: groundwater
User:     gwuser
Password: changeme
```

---

## 📊 Platform Statistics (at a glance)

### Well Coverage
```
Total:    1,196 wells
Active:   1,092 wells (91.3%) ← have forecasts
Unknown:    104 wells (8.7%) ← no data available
```

### Forecast Distribution
```
🔴 Critical:  473 wells (43.3%) ← Declining ≤-2.0 m/year
🟡 Watch:     118 wells (10.8%) ← Declining -2.0 to -0.5 m/year
🟢 Stable:    501 wells (45.9%) ← Stable/Improving >-0.5 m/year
```

### Data Volume
```
Readings:     139,837 measurements
Time Span:    1976 → 2026 (50 years)
Districts:    10+ across Madhya Pradesh
```

---

## 🎯 What Each Status Means

### 🔴 Critical (Red)
- **Trend**: Declining ≥2.0 meters per year
- **Action**: Immediate intervention required
- **Recommendation**: Reduce abstraction, implement managed aquifer recharge
- **Example**: Water table dropping from 500m to 480m in one year

### 🟡 Watch (Yellow)
- **Trend**: Declining 0.5-2.0 meters per year  
- **Action**: Increased monitoring, prepare intervention
- **Recommendation**: Monitor closely, consider recharge structures
- **Example**: Water table dropping from 500m to 495m in one year

### 🟢 Stable (Green)
- **Trend**: Declining <0.5 m/year, stable, or improving
- **Action**: Continue routine monitoring
- **Recommendation**: Maintain current management practices
- **Example**: Water table stable around 500m or recovering

### ⚪ Unknown (Gray)
- **Trend**: No data available
- **Action**: Deploy monitoring equipment
- **Recommendation**: Cannot forecast without historical measurements
- **Example**: Well exists but has never been measured

---

## 🔧 Common Operations

### Check if Services are Running
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### View Backend Logs
```bash
docker-compose logs -f backend
```

### Check Database Connection
```bash
docker exec infra-db-1 psql -U gwuser -d groundwater -c "SELECT COUNT(*) FROM wells;"
# Should return: 1196
```

### Restart a Service
```bash
docker-compose restart backend   # After code changes
docker-compose restart frontend  # After UI changes
```

### Stop Everything
```bash
docker-compose down
```

### Stop + Delete Data
```bash
docker-compose down -v  # ⚠️ WARNING: Deletes database!
```

---

## 📡 API Endpoints (Quick Copy-Paste)

### Get All Wells
```bash
curl -s http://localhost:8000/api/v1/wells | python3 -m json.tool | head -30
```

### Get Specific Well Forecast
```bash
curl -s http://localhost:8000/api/v1/forecast/well/BPL-PZ-08 | python3 -m json.tool
```

### Get Well History
```bash
curl -s http://localhost:8000/api/v1/wells/BPL-PZ-08/history | python3 -m json.tool
```

### Count Wells by Status
```bash
curl -s http://localhost:8000/api/v1/wells | python3 -c "
import sys, json
from collections import Counter
wells = json.load(sys.stdin)
trends = Counter(w.get('trend_label', 'Unknown') for w in wells)
for trend, count in sorted(trends.items()):
    print(f'{trend:12} {count:4}')
"
```

---

## 🗄️ Useful Database Queries

### Connect to Database
```bash
docker exec -it infra-db-1 psql -U gwuser -d groundwater
```

### Count Wells by Status
```sql
SELECT trend_label, COUNT(*) 
FROM wells 
GROUP BY trend_label 
ORDER BY COUNT(*) DESC;
```

### Find Critical Wells in Specific Block
```sql
SELECT well_id, block, trend_label 
FROM wells 
WHERE trend_label = 'Critical' 
  AND block = 'Barasia'
ORDER BY well_id;
```

### Get Recent Readings for a Well
```sql
SELECT date, depth_bgl_m, head_msl_m 
FROM readings 
WHERE well_id = 'BPL-PZ-08' 
ORDER BY date DESC 
LIMIT 10;
```

### Find Wells Near a Location
```sql
SELECT 
  well_id, 
  block,
  ST_Distance(
    geom::geography,
    ST_SetSRID(ST_MakePoint(77.4, 23.6), 4326)::geography
  ) / 1000 as distance_km
FROM wells
ORDER BY distance_km
LIMIT 5;
```

---

## 🛠️ Troubleshooting

### "Could not load wells: Failed to fetch"
```bash
# Check backend is running
curl http://localhost:8000/api/v1/wells

# If empty [], rebuild frontend
cd infra
docker-compose stop frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Map Not Loading
```bash
# Check browser console (F12)
# Common issues:
# 1. Backend not reachable → check docker-compose ps
# 2. CORS error → backend needs CORS_ORIGINS set
# 3. Slow network → map tiles loading from internet
```

### Wells Showing "NaN"
```bash
# Clean up database
docker exec infra-db-1 psql -U gwuser -d groundwater -c "
UPDATE wells SET aquifer_zone = NULL WHERE aquifer_zone IN ('NaN', 'nan', '');
"
```

### Database Connection Refused
```bash
# Check PostgreSQL is healthy
docker exec infra-db-1 pg_isready -U gwuser -d groundwater

# If not ready, restart database
docker-compose restart db
```

---

## 📁 Important Files

### Configuration
```
infra/docker-compose.yml       # Service orchestration
backend/requirements.txt       # Python dependencies
frontend/package.json          # Node.js dependencies
etl/schema.sql                 # Database schema
```

### Application Code
```
backend/app/main.py                        # FastAPI entry point
backend/app/routers/forecast.py            # Forecast endpoints
backend/app/services/statistical_trend.py  # Forecasting logic
frontend/pages/index.tsx                   # Main UI
frontend/components/Map.tsx                # Leaflet map
frontend/lib/api.ts                        # API client
```

### Data Files
```
data/wells.csv          # 1,196 wells metadata
data/water_levels.csv   # 139,837 readings
data/litho.csv          # Lithology data
GW_Data/                # Original .mdb databases (21 files)
```

---

## 🚀 Performance Tips

### Speed Up Map Loading
```sql
-- Pre-cache all trends (run once per data update)
-- Takes ~8 minutes for 1,196 wells
-- See: /tmp/sync_trends.sh
```

### Optimize Database
```sql
-- Rebuild indexes
REINDEX TABLE wells;
REINDEX TABLE readings;

-- Update statistics
ANALYZE wells;
ANALYZE readings;
```

### Monitor Resource Usage
```bash
# Container resource usage
docker stats

# Database connections
docker exec infra-db-1 psql -U gwuser -d groundwater -c "
SELECT count(*) FROM pg_stat_activity WHERE datname = 'groundwater';
"
```

---

## 📚 Documentation Hierarchy

1. **README.md** ← High-level overview + quick start
2. **PROJECT_SUMMARY.md** ← **MAIN DOCUMENTATION** (this session's work)
3. **QUICK_REFERENCE.md** ← This file (commands + cheat sheet)
4. **docs/RUNBOOK.md** ← Detailed deployment guide
5. **docs/API_CONTRACT.md** ← API specifications
6. **docs/PROJECT_PLAN.md** ← Original architecture plan

---

## 🎓 Training / Onboarding

### New Developer Checklist
- [ ] Read README.md (5 min)
- [ ] Read PROJECT_SUMMARY.md (30 min)
- [ ] Run `docker-compose up -d` and test locally (10 min)
- [ ] Browse API docs at http://localhost:8000/docs (10 min)
- [ ] Review database schema: `etl/schema.sql` (15 min)
- [ ] Explore codebase structure (30 min)

### New User (Non-Technical)
1. Open http://localhost:3000
2. Click any colored dot on the map
3. Read the forecast and recommendation
4. That's it! No training needed.

---

## 🔐 Security Notes

### Current State (Development)
```
⚠️  Default credentials: gwuser / changeme
⚠️  No authentication on API
⚠️  No HTTPS (HTTP only)
⚠️  Exposed ports: 3000, 8000, 5432
```

### Production Hardening Checklist
- [ ] Change database password
- [ ] Add API authentication (JWT tokens)
- [ ] Set up HTTPS with SSL certificates
- [ ] Restrict database to internal network only
- [ ] Add rate limiting on API
- [ ] Enable audit logging
- [ ] Set up firewall rules

---

## 📞 Getting Help

| Issue Type | Resource |
|------------|----------|
| How to deploy? | `docs/RUNBOOK.md` |
| API not working? | `docs/API_CONTRACT.md` |
| Database questions? | `etl/schema.sql` + `PROJECT_SUMMARY.md` |
| Understanding the system? | `PROJECT_SUMMARY.md` |
| Quick command needed? | This file (`QUICK_REFERENCE.md`) |

---

**Last Updated**: January 2025  
**For**: Quick reference during development/operations  
**See**: PROJECT_SUMMARY.md for comprehensive documentation
