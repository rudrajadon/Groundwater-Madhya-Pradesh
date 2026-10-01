#!/usr/bin/env python3
"""
Initialize Render PostgreSQL Database with all tables
Run this FIRST before loading data
"""

import psycopg2

DATABASE_URL = "postgresql://groundwater_user:XCmOvmSsepDzDnCRRY9K08ALjA96JGwZ@dpg-dat0ojjncjis73cllkng-a.oregon-postgres.render.com/groundwater_l5m7"

print("=" * 60)
print("INITIALIZING RENDER DATABASE TABLES")
print("=" * 60)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("\n✅ Connected to database successfully!")
    
    # Enable PostGIS
    print("\n📍 Enabling PostGIS extension...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    conn.commit()
    print("   ✅ PostGIS enabled")
    
    # Create wells table
    print("\n🏗️ Creating wells table...")
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
    conn.commit()
    print("   ✅ Wells table created")
    
    # Create index on wells
    print("\n📊 Creating wells spatial index...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_wells_geom ON wells USING GIST (geom);")
    conn.commit()
    print("   ✅ Spatial index created")
    
    # Create readings table
    print("\n🏗️ Creating readings table...")
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
    conn.commit()
    print("   ✅ Readings table created")
    
    # Create index on readings
    print("\n📊 Creating readings indexes...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_readings_well_date ON readings(well_id, date);")
    conn.commit()
    print("   ✅ Readings indexes created")
    
    # Create lithology table
    print("\n🏗️ Creating lithology_logs table...")
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
    conn.commit()
    print("   ✅ Lithology table created")
    
    # Create rainfall stations table
    print("\n🏗️ Creating rainfall_stations table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rainfall_stations (
            station_name    TEXT PRIMARY KEY,
            geom            GEOGRAPHY(POINT, 4326)
        );
    """)
    conn.commit()
    print("   ✅ Rainfall stations table created")
    
    # Create rainfall readings table
    print("\n🏗️ Creating rainfall_readings table...")
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
    conn.commit()
    print("   ✅ Rainfall readings table created")
    
    # Create admin boundaries table
    print("\n🏗️ Creating admin_boundaries table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_boundaries (
            id              SERIAL PRIMARY KEY,
            level           TEXT,
            name            TEXT,
            geom            GEOGRAPHY(GEOMETRY, 4326)
        );
    """)
    conn.commit()
    print("   ✅ Admin boundaries table created")
    
    # Create model versions table
    print("\n🏗️ Creating model_versions table...")
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
    conn.commit()
    print("   ✅ Model versions table created")
    
    # Verify all tables
    print("\n📋 Verifying tables...")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    
    print(f"\n✅ Found {len(tables)} tables:")
    for table in tables:
        print(f"   - {table[0]}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ DATABASE INITIALIZED SUCCESSFULLY!")
    print("=" * 60)
    print("\n🚀 Next step: Run load_real_data_to_render.py to load your data")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
