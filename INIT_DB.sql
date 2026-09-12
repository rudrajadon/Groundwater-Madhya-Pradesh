-- Initialize Render Database for MP Groundwater Monitor
-- Copy and paste this entire file into psql

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

-- Create lithology table
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

-- Create rainfall stations
CREATE TABLE IF NOT EXISTS rainfall_stations (
    station_name    TEXT PRIMARY KEY,
    geom            GEOGRAPHY(POINT, 4326)
);

-- Create rainfall readings
CREATE TABLE IF NOT EXISTS rainfall_readings (
    id              SERIAL PRIMARY KEY,
    station_name    TEXT REFERENCES rainfall_stations(station_name),
    date            DATE NOT NULL,
    rainfall_mm     NUMERIC,
    source          TEXT DEFAULT 'mdb_import',
    CONSTRAINT uq_rainfall_station_date UNIQUE (station_name, date)
);

CREATE INDEX IF NOT EXISTS idx_rainfall_station_date ON rainfall_readings(station_name, date);

-- Create admin boundaries
CREATE TABLE IF NOT EXISTS admin_boundaries (
    id              SERIAL PRIMARY KEY,
    level           TEXT,
    name            TEXT,
    geom            GEOGRAPHY(GEOMETRY, 4326)
);

-- Create model versions
CREATE TABLE IF NOT EXISTS model_versions (
    version_id      TEXT PRIMARY KEY,
    trained_on      DATE,
    rmse            NUMERIC,
    r2              NUMERIC,
    nse             NUMERIC,
    artifact_path   TEXT,
    is_active       BOOLEAN DEFAULT FALSE
);

-- Insert sample wells for testing
INSERT INTO wells (well_id, district, block, lat_raw, lon_raw, geom, aquifer_zone, trend_label, geology_type, aquifer_classification)
VALUES
  ('INDORE-W001', 'Indore', 'Indore', '22.7196', '75.8577', ST_GeogFromText('POINT(75.8577 22.7196)'), 'Weathered', 'Stable', 'Basalt', 'Weathered'),
  ('INDORE-W002', 'Indore', 'Mhow', '22.5469', '75.7607', ST_GeogFromText('POINT(75.7607 22.5469)'), 'Fractured', 'Watch', 'Basalt', 'Fractured'),
  ('INDORE-W003', 'Indore', 'Depalpur', '22.8508', '75.5426', ST_GeogFromText('POINT(75.5426 22.8508)'), 'Weathered', 'Critical', 'Granite', 'Weathered'),
  ('UJJAIN-W001', 'Ujjain', 'Ujjain', '23.1765', '75.7885', ST_GeogFromText('POINT(75.7885 23.1765)'), 'Massive', 'Stable', 'Basalt', 'Massive'),
  ('BHOPAL-W001', 'Bhopal', 'Bhopal', '23.2599', '77.4126', ST_GeogFromText('POINT(77.4126 23.2599)'), 'Fractured', 'Watch', 'Vindhyan', 'Fractured'),
  ('JABALPUR-W001', 'Jabalpur', 'Jabalpur', '23.1815', '79.9864', ST_GeogFromText('POINT(79.9864 23.1815)'), 'Weathered', 'Stable', 'Granite', 'Weathered'),
  ('GWALIOR-W001', 'Gwalior', 'Gwalior', '26.2183', '78.1828', ST_GeogFromText('POINT(78.1828 26.2183)'), 'Fractured', 'Critical', 'Vindhyan', 'Fractured'),
  ('SAGAR-W001', 'Sagar', 'Sagar', '23.8388', '78.7378', ST_GeogFromText('POINT(78.7378 23.8388)'), 'Weathered', 'Watch', 'Basalt', 'Weathered')
ON CONFLICT (well_id) DO NOTHING;

-- Verify data
SELECT 'Tables created successfully!' AS status;
SELECT COUNT(*) AS well_count FROM wells;
SELECT well_id, district, trend_label FROM wells ORDER BY well_id;
