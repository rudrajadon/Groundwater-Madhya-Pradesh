# Setup Guide

Complete setup instructions for the Groundwater Forecast System.

## 📋 Prerequisites

### Required Software
- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
  - OR Python 3.11+, Node.js 20+, PostgreSQL 16 with PostGIS

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 5GB free space (includes database and ML models)
- **OS**: Linux, macOS, or Windows with WSL2

## 🚀 Quick Start (Docker)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/groundwater-app.git
cd groundwater-app
```

### 2. Start Services
```bash
cd infra
docker-compose up -d
```

### 3. Wait for Initialization
Services take about 30-60 seconds to become healthy:
```bash
# Check service status
docker-compose ps

# Watch logs
docker-compose logs -f
```

### 4. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🛠️ Manual Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://gwuser:changeme@localhost:5432/groundwater"
export MODEL_ARTIFACT_DIR="../ml/artifacts"

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local

# Development server
npm run dev

# Production build
npm run build
npm start
```

### Database Setup

```bash
# Install PostgreSQL with PostGIS
brew install postgresql@16 postgis  # macOS
# OR
sudo apt install postgresql-16 postgis  # Ubuntu

# Create database
createdb groundwater
psql groundwater -c "CREATE EXTENSION postgis;"

# Load schema
psql groundwater < etl/schema.sql

# Load data
cd etl
python load_to_postgres.py
```

## 🗄️ Data Pipeline Setup

### Extract Data from MS Access

```bash
cd etl

# Install mdbtools (Linux/macOS)
brew install mdbtools  # macOS
sudo apt install mdbtools  # Ubuntu

# Export all MDB files
./export_mdb.sh
```

### Process and Load Data

```bash
# Create ETL virtual environment
python -m venv etl_venv
source etl_venv/bin/activate

# Install ETL dependencies
pip install -r requirements.txt

# Parse coordinates from station names
python parse_coordinates.py

# Fetch rainfall data (optional - takes ~1 hour)
python fetch_rainfall_openmeteo.py

# Load everything to PostgreSQL
python load_to_postgres.py
```

## 🐳 Docker Configuration

### Environment Variables

Create `infra/.env` file:
```bash
# Database
POSTGRES_DB=groundwater
POSTGRES_USER=gwuser
POSTGRES_PASSWORD=changeme

# Backend
DATABASE_URL=postgresql://gwuser:changeme@db:5432/groundwater
MODEL_ARTIFACT_DIR=/app/ml/artifacts

# Frontend
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### Custom Ports

Edit `infra/docker-compose.yml`:
```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # Change 3001 to your desired port
  
  backend:
    ports:
      - "8001:8000"  # Change 8001 to your desired port
```

### Volume Mounting

For development with hot-reload:
```yaml
services:
  backend:
    volumes:
      - ../backend/app:/app/app
  
  frontend:
    volumes:
      - ../frontend:/app
      - /app/node_modules
```

## 🔧 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps db

# Check logs
docker-compose logs db

# Connect manually
docker-compose exec db psql -U gwuser -d groundwater

# Test query
SELECT COUNT(*) FROM wells;
```

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend

# Clear browser cache (Cmd+Shift+R)
```

### Backend Errors

```bash
# Check backend logs
docker-compose logs backend

# Verify ML model exists
ls -lh ml/artifacts/

# Test API directly
curl http://localhost:8000/api/v1/wells | jq
```

### Port Already in Use

```bash
# Find process using port
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # Database

# Kill process
kill -9 <PID>

# Or change ports in docker-compose.yml
```

## 🧪 Verify Installation

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# Get wells
curl http://localhost:8000/api/v1/wells | jq '.[:5]'

# Get forecast
curl http://localhost:8000/api/v1/forecast/well/SIND-PTW%2038-PZ | jq
```

### Test Frontend

1. Open http://localhost:3000
2. Click on any well marker
3. View forecast chart
4. Click "Generate Report"
5. Generate PDF

### Test Database

```bash
docker-compose exec db psql -U gwuser -d groundwater -c "\dt"
docker-compose exec db psql -U gwuser -d groundwater -c "SELECT COUNT(*) FROM wells;"
```

## 🔄 Updating

### Update Code

```bash
git pull origin main

# Rebuild containers
cd infra
docker-compose down
docker-compose build
docker-compose up -d
```

### Update Database Schema

```bash
# Backup existing data
docker-compose exec db pg_dump -U gwuser groundwater > backup.sql

# Apply schema changes
docker-compose exec db psql -U gwuser -d groundwater < etl/schema.sql

# Reload data if needed
cd etl
python load_to_postgres.py
```

### Update ML Model

```bash
# Copy new model artifacts
cp /path/to/new/model/* ml/artifacts/

# Restart backend
docker-compose restart backend
```

## 📊 Performance Tuning

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_wells_district ON wells(district);
CREATE INDEX idx_readings_well_date ON water_level_readings(well_id, date);

-- Analyze tables
ANALYZE wells;
ANALYZE water_level_readings;
```

### Backend Optimization

```python
# Edit backend/app/main.py
# Adjust worker count
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Frontend Optimization

```bash
# Production build with optimizations
cd frontend
npm run build
```

## 🔐 Production Deployment

### Security Checklist

- [ ] Change default database password
- [ ] Enable HTTPS/TLS
- [ ] Add authentication (Clerk, Auth0, etc.)
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Add CORS configuration
- [ ] Use environment-specific configs
- [ ] Enable logging and monitoring
- [ ] Set up backup system
- [ ] Use secrets management

### Recommended Stack

- **Hosting**: AWS, GCP, or Azure
- **Database**: Managed PostgreSQL (RDS, Cloud SQL)
- **Frontend**: Vercel or Netlify
- **Backend**: Docker on ECS/GKE/AKS
- **SSL**: Let's Encrypt
- **CDN**: CloudFlare
- **Monitoring**: Datadog, New Relic

## 📞 Support

If you encounter issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Search [GitHub Issues](https://github.com/yourusername/groundwater-app/issues)
3. Create a new issue with:
   - Error messages
   - Steps to reproduce
   - System information
   - Relevant logs

## 📚 Next Steps

- Read [API_CONTRACT.md](docs/API_CONTRACT.md) for API documentation
- Check [RUNBOOK.md](docs/RUNBOOK.md) for detailed operations guide
- See [CONTRIBUTING.md](CONTRIBUTING.md) to start contributing
- Review [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) for roadmap
