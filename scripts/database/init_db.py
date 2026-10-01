#!/usr/bin/env python3
"""
Initialize Render PostgreSQL Database
Run: python3 init_db.py
"""

import psycopg2

# Database connection
DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

print("🔌 Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("📊 Creating tables...")

# Enable PostGIS
cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
print("✅ PostGIS enabled")

# Create wells table
cur.execute("""
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
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_wells_geom ON wells USING GIST (geom);")
print("✅ Wells table created")

# Create readings table
cur.execute("""
CREATE TABLE IF NOT EXISTS readings (
    id              SERIAL PRIMARY KEY,
    well_id         TEXT REFERENCES wells(well_id),
    date            DATE NOT NULL,
    depth_bgl_m     NUMERIC,
    head_msl_m      NUMERIC,
    source          TEXT DEFAULT 'mdb_import',
    CONSTRAINT uq_readings_well_date UNIQUE (well_id, date)
);
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_readings_well_date ON readings(well_id, date);")
print("✅ Readings table created")

# Create other tables
cur.execute("""
CREATE TABLE IF NOT EXISTS lithology_logs (
    id              SERIAL PRIMARY KEY,
    well_id         TEXT REFERENCES wells(well_id),
    depth_to_m      NUMERIC,
    lyr_id          TEXT,
    lithology       TEXT,
    colour          TEXT,
    texture         TEXT
);
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_litho_well ON lithology_logs(well_id);")

cur.execute("""
CREATE TABLE IF NOT EXISTS rainfall_stations (
    station_name    TEXT PRIMARY KEY,
    geom            GEOGRAPHY(POINT, 4326)
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS rainfall_readings (
    id              SERIAL PRIMARY KEY,
    station_name    TEXT REFERENCES rainfall_stations(station_name),
    date            DATE NOT NULL,
    rainfall_mm     NUMERIC,
    source          TEXT DEFAULT 'mdb_import',
    CONSTRAINT uq_rainfall_station_date UNIQUE (station_name, date)
);
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_rainfall_station_date ON rainfall_readings(station_name, date);")

cur.execute("""
CREATE TABLE IF NOT EXISTS admin_boundaries (
    id              SERIAL PRIMARY KEY,
    level           TEXT,
    name            TEXT,
    geom            GEOGRAPHY(GEOMETRY, 4326)
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS model_versions (
    version_id      TEXT PRIMARY KEY,
    trained_on      DATE,
    rmse            NUMERIC,
    r2              NUMERIC,
    nse             NUMERIC,
    artifact_path   TEXT,
    is_active       BOOLEAN DEFAULT FALSE
);
""")
print("✅ All tables created")

print("\n📊 Inserting sample wells...")

# Insert sample data
wells_data = [
    ("INDORE-W001", "Indore", "Indore", "22.7196", "75.8577", "Weathered", "Stable", "Basalt", "Weathered"),
    ("INDORE-W002", "Indore", "Mhow", "22.5469", "75.7607", "Fractured", "Watch", "Basalt", "Fractured"),
    ("INDORE-W003", "Indore", "Depalpur", "22.8508", "75.5426", "Weathered", "Critical", "Granite", "Weathered"),
    ("UJJAIN-W001", "Ujjain", "Ujjain", "23.1765", "75.7885", "Massive", "Stable", "Basalt", "Massive"),
    ("BHOPAL-W001", "Bhopal", "Bhopal", "23.2599", "77.4126", "Fractured", "Watch", "Vindhyan", "Fractured"),
    ("JABALPUR-W001", "Jabalpur", "Jabalpur", "23.1815", "79.9864", "Weathered", "Stable", "Granite", "Weathered"),
    ("GWALIOR-W001", "Gwalior", "Gwalior", "26.2183", "78.1828", "Fractured", "Critical", "Vindhyan", "Fractured"),
    ("SAGAR-W001", "Sagar", "Sagar", "23.8388", "78.7378", "Weathered", "Watch", "Basalt", "Weathered"),
]

for well_id, district, block, lat, lon, aquifer, trend, geology, classification in wells_data:
    cur.execute("""
        INSERT INTO wells (well_id, district, block, lat_raw, lon_raw, geom, aquifer_zone, trend_label, geology_type, aquifer_classification)
        VALUES (%s, %s, %s, %s, %s, ST_GeogFromText('POINT(' || %s || ' ' || %s || ')'), %s, %s, %s, %s)
        ON CONFLICT (well_id) DO NOTHING
    """, (well_id, district, block, lat, lon, lon, lat, aquifer, trend, geology, classification))
    print(f"  ✅ {well_id}")

conn.commit()

# Verify
cur.execute("SELECT COUNT(*) FROM wells")
count = cur.fetchone()[0]
print(f"\n✅ Database initialized! {count} wells inserted")

# Show sample data
print("\n📋 Sample wells:")
cur.execute("SELECT well_id, district, trend_label FROM wells ORDER BY well_id LIMIT 5")
for row in cur.fetchall():
    print(f"  • {row[0]} - {row[1]} - {row[2]}")

cur.close()
conn.close()

print("\n🎉 Done! Database is ready!")
print("\n🧪 Test the API:")
print("https://mp-groundwater-backend.onrender.com/api/v1/wells")
