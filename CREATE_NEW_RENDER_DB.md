# Create New PostgreSQL Database on Render

## 🎯 Quick Steps

### 1. Create Database

1. Go to: https://dashboard.render.com/
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name:** `mp-groundwater-db-new`
   - **Database:** `groundwater`
   - **User:** `groundwater_user`
   - **Region:** `Oregon (US West)` (same as backend)
   - **PostgreSQL Version:** 16
   - **Plan:** Free
4. Click **"Create Database"**
5. **WAIT 2-3 minutes** for database to provision

---

### 2. Get Database URL

Once database shows **"Available"**:

1. Click on the database name
2. Go to **"Connect"** tab
3. **Copy the "Internal Database URL"**

Should look like:
```
postgresql://groundwater_user:LONG_PASSWORD@dpg-NEWID-a.oregon-postgres.render.com/groundwater
```

---

### 3. Update Backend Environment Variable

1. Go to **mp-groundwater-backend-z6hh** service
2. Click **"Environment"** (left sidebar)
3. Find `DATABASE_URL`
4. Click **Edit**
5. **Paste the new Internal Database URL**
6. Click **"Save Changes"**

Service will auto-restart (~30 seconds)

---

### 4. Initialize Database Tables

Once backend restarts successfully, run this to create tables:

1. Go back to PostgreSQL database dashboard
2. Click **"Connect"** tab
3. Click **"Open PSQL"** button (opens terminal in browser)
4. Paste this SQL:

```sql
-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create wells table
CREATE TABLE IF NOT EXISTS wells (
    well_id         TEXT PRIMARY KEY,
    well_type       TEXT,
    agency          TEXT,
    district        TEXT,
    tahsil          TEXT,
    block           TEXT,
    village         TEXT,
    geom            GEOGRAPHY(POINT, 4326),
    lat_raw         TEXT,
    lon_raw         TEXT,
    coord_validated BOOLEAN DEFAULT FALSE,
    elevation_m     NUMERIC,
    command_area    NUMERIC,
    aquifer_zone    TEXT,
    wthr_pct        NUMERIC,
    frac_pct        NUMERIC,
    mass_pct        NUMERIC,
    dwlr_installed  BOOLEAN,
    dwlr_no         TEXT,
    source_file     TEXT,
    trend_label     TEXT,
    geology_type    TEXT,
    aquifer_classification TEXT
);

CREATE INDEX IF NOT EXISTS idx_wells_geom ON wells USING GIST (geom);

-- Create readings table
CREATE TABLE IF NOT EXISTS readings (
    id              SERIAL PRIMARY KEY,
    well_id         TEXT REFERENCES wells(well_id),
    date            DATE NOT NULL,
    depth_bgl_m     NUMERIC,
    head_msl_m      NUMERIC,
    source          TEXT DEFAULT 'mdb_import',
    CONSTRAINT uq_readings_well_date UNIQUE (well_id, date)
);

CREATE INDEX IF NOT EXISTS idx_readings_well_date ON readings(well_id, date);

-- Sample test well
INSERT INTO wells (well_id, district, block, lat_raw, lon_raw, geom, aquifer_zone, trend_label, geology_type)
VALUES ('TEST-001', 'Indore', 'Indore', '22.7196', '75.8577', 
        ST_GeogFromText('POINT(75.8577 22.7196)'), 'Weathered', 'Stable', 'Basalt')
ON CONFLICT (well_id) DO NOTHING;
```

5. Press Enter and wait for "CREATE TABLE" confirmations

---

### 5. Verify Backend Works

```bash
# Test health
curl https://mp-groundwater-backend-z6hh.onrender.com/health

# Test wells endpoint
curl https://mp-groundwater-backend-z6hh.onrender.com/api/v1/wells

# Should return JSON with TEST-001 well
```

---

## ✅ Success Checklist

- [ ] New database created and shows "Available"
- [ ] Internal Database URL copied
- [ ] DATABASE_URL updated in backend environment
- [ ] Backend restarted (check logs for "Application startup complete")
- [ ] No database connection errors in logs
- [ ] Tables created via PSQL
- [ ] `/health` endpoint returns `{"status":"healthy"}`
- [ ] `/api/v1/wells` returns test well data

---

## 🆘 If Issues Persist

Check backend logs for:
- ✅ "Database connection successful"
- ❌ "failed to resolve host" → DATABASE_URL is wrong
- ❌ "password authentication failed" → Password typo in URL

**The database URL MUST be the Internal URL, not External!**
