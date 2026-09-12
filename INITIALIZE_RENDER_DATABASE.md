# 🗄️ Initialize Render PostgreSQL Database

## Current Status
✅ Database created: `mp-groundwater-db`  
✅ Database URL added to backend  
⏳ Need to: Create tables and load data

---

## 🎯 Option 1: Use Render Dashboard (Easiest)

### Step 1: Open Database Shell

1. Go to Render Dashboard
2. Click on **`mp-groundwater-db`** database
3. Click **"Connect"** tab
4. Click **"Open PSQL"** button
5. A terminal will open connected to your database

### Step 2: Create Tables

Copy and paste this SQL:

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

-- Create other tables
CREATE TABLE IF NOT EXISTS lithology_logs (
    id              SERIAL PRIMARY KEY,
    well_id         TEXT REFERENCES wells(well_id),
    depth_to_m      NUMERIC,
    lyr_id          TEXT,
    lithology       TEXT,
    colour          TEXT,
    texture         TEXT
);

CREATE INDEX IF NOT EXISTS idx_litho_well ON lithology_logs(well_id);

CREATE TABLE IF NOT EXISTS rainfall_stations (
    station_name    TEXT PRIMARY KEY,
    geom            GEOGRAPHY(POINT, 4326)
);

CREATE TABLE IF NOT EXISTS rainfall_readings (
    id              SERIAL PRIMARY KEY,
    station_name    TEXT REFERENCES rainfall_stations(station_name),
    date            DATE NOT NULL,
    rainfall_mm     NUMERIC,
    source          TEXT DEFAULT 'mdb_import',
    CONSTRAINT uq_rainfall_station_date UNIQUE (station_name, date)
);

CREATE INDEX IF NOT EXISTS idx_rainfall_station_date ON rainfall_readings(station_name, date);

CREATE TABLE IF NOT EXISTS admin_boundaries (
    id              SERIAL PRIMARY KEY,
    level           TEXT,
    name            TEXT,
    geom            GEOGRAPHY(GEOMETRY, 4326)
);

CREATE TABLE IF NOT EXISTS model_versions (
    version_id      TEXT PRIMARY KEY,
    trained_on      DATE,
    rmse            NUMERIC,
    r2              NUMERIC,
    nse             NUMERIC,
    artifact_path   TEXT,
    is_active       BOOLEAN DEFAULT FALSE
);
```

Press Enter and wait for "CREATE TABLE" confirmations.

### Step 3: Verify Tables Created

```sql
\dt
```

Should show all tables! ✅

---

## 📊 Option 2: Load Sample Data (For Testing)

For now, let's add some sample wells so the frontend can display something:

```sql
-- Insert sample wells
INSERT INTO wells (well_id, district, block, lat_raw, lon_raw, geom, aquifer_zone, trend_label, geology_type, aquifer_classification)
VALUES
  ('WELL001', 'Indore', 'Indore', '22.7196', '75.8577', ST_GeogFromText('POINT(75.8577 22.7196)'), 'Weathered', 'Stable', 'Basalt', 'Weathered'),
  ('WELL002', 'Indore', 'Mhow', '22.5469', '75.7607', ST_GeogFromText('POINT(75.7607 22.5469)'), 'Fractured', 'Watch', 'Basalt', 'Fractured'),
  ('WELL003', 'Indore', 'Depalpur', '22.8508', '75.5426', ST_GeogFromText('POINT(75.5426 22.8508)'), 'Weathered', 'Critical', 'Granite', 'Weathered'),
  ('WELL004', 'Ujjain', 'Ujjain', '23.1765', '75.7885', ST_GeogFromText('POINT(75.7885 23.1765)'), 'Massive', 'Stable', 'Basalt', 'Massive'),
  ('WELL005', 'Bhopal', 'Bhopal', '23.2599', '77.4126', ST_GeogFromText('POINT(77.4126 23.2599)'), 'Fractured', 'Watch', 'Vindhyan', 'Fractured')
ON CONFLICT (well_id) DO NOTHING;

-- Verify wells inserted
SELECT well_id, district, aquifer_zone, trend_label FROM wells;
```

Should show 5 sample wells! ✅

---

## 🚀 After Tables Are Created

1. **Check Backend Logs** - Should see database connection success
2. **Test API Endpoint**:
   ```
   https://mp-groundwater-backend.onrender.com/api/v1/wells
   ```
   Should return JSON with the 5 sample wells!

3. **Test Frontend**:
   ```
   https://groundwater-madhya-pradesh.vercel.app/mpgroundwatermonitor
   ```
   Map should load with 5 wells! 🎉

---

## 📊 Later: Load Full Dataset

Once this works, you can load your full dataset using the ETL scripts:

```bash
# From your local machine
cd /Users/rudrajadon/Downloads/groundwater-app/etl
python load_data.py
```

But for now, sample data is enough to verify deployment! ✅

---

## 🆘 If PSQL Button Not Available

Use command line connection:

```bash
# Get connection string from Render dashboard
# Should look like: postgresql://user:pass@host:5432/dbname

psql "YOUR_EXTERNAL_DATABASE_URL"

# Then paste the CREATE TABLE statements above
```

---

**Go to Render Dashboard → mp-groundwater-db → Connect → Open PSQL**

Then paste the SQL and let me know when tables are created! 🚀
