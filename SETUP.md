# Setup Guide

Complete setup instructions for the Madhya Pradesh Groundwater Monitoring System.

## Development Environment Setup

### 1. System Requirements

- **Operating System:** macOS, Linux, or Windows with WSL2
- **Node.js:** 18.x or higher
- **Python:** 3.11 or higher
- **PostgreSQL:** 14.x or higher with PostGIS extension
- **Git:** For version control
- **Docker:** (Optional) For containerized deployment

### 2. Clone Repository

```bash
git clone https://github.com/rudrajadon/Groundwater-Madhya-Pradesh.git
cd Groundwater-Madhya-Pradesh
```

### 3. Database Setup

#### Install PostgreSQL with PostGIS

**macOS:**
```bash
brew install postgresql@14 postgis
brew services start postgresql@14
```

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql-14 postgresql-14-postgis-3
sudo systemctl start postgresql
```

#### Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create user and database
CREATE USER groundwater_user WITH PASSWORD 'your_password';
CREATE DATABASE groundwater_db OWNER groundwater_user;

# Connect to the database and enable PostGIS
\c groundwater_db
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE groundwater_db TO groundwater_user;
\q
```

#### Initialize Schema

```bash
cd scripts/database
python init_db.py
```

### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://groundwater_user:your_password@localhost:5432/groundwater_db
SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000
MODEL_ARTIFACT_DIR=../ml/artifacts
EOF

# Test the backend
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs to see the API documentation.

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_API_BASE=http://localhost:8000
EOF

# Run development server
npm run dev
```

Visit http://localhost:3000/mpgroundwater/ to see the application.

### 6. Load Data

#### Load Wells
```bash
python scripts/data_processing/load_all_wells_to_render.py
```

#### Load Water Level Readings
```bash
python scripts/data_processing/load_readings_only.py
```

#### Calculate Trends
```bash
python scripts/database/update_well_trends.py
```

## Production Deployment

### Render.com (Backend)

1. **Create PostgreSQL Database**
   - Go to Render Dashboard → New → PostgreSQL
   - Name: `groundwater-db`
   - Plan: Free or Starter
   - Note the connection string

2. **Create Web Service**
   - Go to Render Dashboard → New → Web Service
   - Connect your GitHub repository
   - Settings:
     - **Name:** `mp-groundwater-backend`
     - **Runtime:** Docker
     - **Root Directory:** `backend`
     - **Region:** Choose closest to your users
     - **Branch:** main

3. **Environment Variables**
   ```
   DATABASE_URL=<your_postgres_connection_string>
   SECRET_KEY=<random_secret_key>
   ENVIRONMENT=production
   ALLOWED_ORIGINS=https://www.rudrajadon.in
   ```

4. **Deploy**
   - Render will automatically build and deploy
   - Note the backend URL (e.g., https://mp-groundwater-backend.onrender.com)

### Vercel (Frontend)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy**
   ```bash
   cd frontend
   vercel --prod
   ```

3. **Environment Variables**
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_BASE=https://mp-groundwater-backend.onrender.com`
   - Redeploy

### Post-Deployment

1. **Load Data to Production Database**
   ```bash
   # Update DATABASE_URL to production in scripts
   python scripts/data_processing/load_all_wells_to_render.py
   python scripts/data_processing/load_readings_only.py
   python scripts/database/update_well_trends.py
   ```

2. **Test Endpoints**
   ```bash
   curl https://mp-groundwater-backend.onrender.com/health
   curl https://mp-groundwater-backend.onrender.com/api/v1/wells | jq
   ```

## Machine Learning Model Setup

### Training the Model

```bash
cd ml

# Activate Python environment
source ../.venv/bin/activate

# Run training
python train.py --epochs 100 --batch-size 32

# Artifacts will be saved to ml/artifacts/
```

### Using Pre-trained Model

1. Ensure `ml/artifacts/` contains:
   - `model_metadata.json`
   - `best_model.pth`
   - `scalers/` directory with well-specific scalers

2. Backend will automatically load the model on startup

## Troubleshooting

### Backend Won't Start

**Error: `ModuleNotFoundError: No module named 'psycopg'`**
- Solution: Install psycopg3: `pip install psycopg[binary]`

**Error: Database connection failed**
- Check DATABASE_URL is correct
- Ensure PostgreSQL is running
- Verify PostGIS extension is enabled

### Frontend Won't Load

**Error: API requests failing**
- Check NEXT_PUBLIC_API_BASE in .env.local
- Ensure backend is running
- Check browser console for CORS errors

**Error: Module not found**
- Delete node_modules and package-lock.json
- Run `npm install` again

### Data Loading Issues

**Error: Foreign key constraint violation**
- Load wells before readings
- Ensure well IDs in readings match wells table

**Error: No such column**
- Run `python scripts/database/add_forecast_columns.py`
- This adds missing forecast_cache and forecast_decline_m columns

## Development Tips

### Hot Reload

Both backend and frontend support hot reload:
- Backend: FastAPI auto-reloads on file changes
- Frontend: Next.js hot module replacement (HMR)

### Database Migrations

When changing database schema:
1. Update models in `backend/app/db.py`
2. Create migration script in `scripts/database/`
3. Run migration on dev and production

### Adding New API Endpoints

1. Create router in `backend/app/routers/`
2. Import in `backend/app/main.py`
3. Update API documentation

### Adding New Pages

1. Create page in `frontend/pages/`
2. Add navigation link if needed
3. Remember the base path: `/mpgroundwater`

## Monitoring and Maintenance

### Check Application Health

```bash
# Backend health
curl https://mp-groundwater-backend.onrender.com/health

# Check database connection
python scripts/database/diagnose_database.py
```

### Update Trends

Run weekly to update trend labels:
```bash
python scripts/database/update_well_trends.py
```

### Backup Database

```bash
# Render automatically backs up PostgreSQL
# Manual backup:
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [Render Deployment Guide](https://render.com/docs)
- [Vercel Deployment Guide](https://vercel.com/docs)
