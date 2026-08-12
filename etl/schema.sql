-- Groundwater App: PostgreSQL + PostGIS schema
-- Run: psql -d groundwater -f schema.sql
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS wells (
    well_id         TEXT PRIMARY KEY,
    well_type       TEXT,
    agency          TEXT,
    district        TEXT,
    tahsil          TEXT,
    block           TEXT,
    village         TEXT,
    geom            GEOGRAPHY(POINT, 4326),
    lat_raw         TEXT,          -- original DMS string, kept for audit
    lon_raw         TEXT,
    coord_validated BOOLEAN DEFAULT FALSE,
    elevation_m     NUMERIC,
    command_area    NUMERIC,
    aquifer_zone    TEXT,          -- 'Weathered' | 'Fractured' | 'Massive' | 'Other'
    wthr_pct        NUMERIC,
    frac_pct        NUMERIC,
    mass_pct        NUMERIC,
    dwlr_installed  BOOLEAN,
    dwlr_no         TEXT,
    source_file     TEXT,          -- source MDB filename for audit trail
    trend_label     TEXT,          -- 'Stable' | 'Watch' | 'Critical'
    geology_type    TEXT,          -- 'Basalt' | 'Granite' | 'Vindhyan' | 'Unknown'
    aquifer_classification TEXT    -- 'Weathered' | 'Fractured' | 'Massive'
);
CREATE INDEX IF NOT EXISTS idx_wells_geom ON wells USING GIST (geom);

CREATE TABLE IF NOT EXISTS readings (
    id              SERIAL PRIMARY KEY,
    well_id         TEXT REFERENCES wells(well_id),
    date            DATE NOT NULL,
    depth_bgl_m     NUMERIC,
    head_msl_m      NUMERIC,       -- elevation_m - depth_bgl_m, computed at load time
    source          TEXT DEFAULT 'mdb_import',  -- 'mdb_import' | 'dwlr' | 'manual'
    CONSTRAINT uq_readings_well_date UNIQUE (well_id, date)
);
CREATE INDEX IF NOT EXISTS idx_readings_well_date ON readings(well_id, date);

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
    source          TEXT DEFAULT 'mdb_import',  -- 'mdb_import' | 'open_meteo'
    CONSTRAINT uq_rainfall_station_date UNIQUE (station_name, date)
);
CREATE INDEX IF NOT EXISTS idx_rainfall_station_date ON rainfall_readings(station_name, date);

CREATE TABLE IF NOT EXISTS admin_boundaries (
    id              SERIAL PRIMARY KEY,
    level           TEXT,           -- 'block' | 'village'
    name            TEXT,
    geom            GEOGRAPHY(GEOMETRY, 4326)
);

CREATE TABLE IF NOT EXISTS model_versions (
    version_id      TEXT PRIMARY KEY,   -- e.g. 'pgnn_v3_2025_08'
    trained_on      DATE,
    rmse            NUMERIC,
    r2              NUMERIC,
    nse             NUMERIC,
    artifact_path   TEXT,
    is_active       BOOLEAN DEFAULT FALSE
);
