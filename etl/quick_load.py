#!/usr/bin/env python3
"""Quick load wells and readings from CSV to restore database."""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import sys

DATABASE_URL = "postgresql://gwuser:changeme@localhost:5432/groundwater"

def load_wells():
    print("Loading wells...")
    df = pd.read_csv("../data/wells.csv")
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    rows = []
    for _, r in df.iterrows():
        well_id = str(r["Well No"]).strip()
        lat = r["Northing"]
        lon = r["Easting"]
        
        rows.append((
            well_id,
            r.get("Well Type"),
            r.get("District"),
            r.get("Tahsil / Taluk"),
            r.get("Block / Mandal"),
            r.get("Village"),
            lon, lat,  # ST_SetSRID(ST_MakePoint(lon, lat), 4326)
            r.get("Elevation of Ground Level"),
            r.get("Aquifer Zone"),
            r.get("Command Area"),
            r.get("Coord Validated"),
            r.get("geology_type"),
            r.get("aquifer_classification")
        ))
    
    execute_values(cur, """
        INSERT INTO wells (
            well_id, well_type, district, tahsil, block, village,
            geom, elevation_m, aquifer_zone, command_area, coord_validated,
            geology_type, aquifer_classification
        ) VALUES %s
        ON CONFLICT (well_id) DO UPDATE SET
            well_type = EXCLUDED.well_type,
            district = EXCLUDED.district,
            tahsil = EXCLUDED.tahsil,
            block = EXCLUDED.block,
            village = EXCLUDED.village,
            geom = EXCLUDED.geom,
            elevation_m = EXCLUDED.elevation_m,
            aquifer_zone = EXCLUDED.aquifer_zone,
            command_area = EXCLUDED.command_area,
            coord_validated = EXCLUDED.coord_validated,
            geology_type = EXCLUDED.geology_type,
            aquifer_classification = EXCLUDED.aquifer_classification
    """, rows, template="(%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, %s, %s, %s)")
    
    conn.commit()
    print(f"✓ Loaded {len(rows)} wells")
    cur.close()
    conn.close()

def load_readings():
    print("Loading water level readings...")
    df = pd.read_csv("../data/water_levels.csv")
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    rows = []
    for _, r in df.iterrows():
        rows.append((
            r["Well No"],
            r["date"],
            r.get("Water Level"),
            r.get("head_msl_m"),
            "csv_import"
        ))
    
    print(f"Inserting {len(rows)} readings...")
    execute_values(cur, """
        INSERT INTO readings (well_id, date, depth_bgl_m, head_msl_m, source)
        VALUES %s
        ON CONFLICT (well_id, date) DO UPDATE SET
            depth_bgl_m = EXCLUDED.depth_bgl_m,
            head_msl_m = EXCLUDED.head_msl_m
    """, rows)
    
    conn.commit()
    print(f"✓ Loaded {len(rows)} readings")
    cur.close()
    conn.close()

if __name__ == "__main__":
    try:
        load_wells()
        load_readings()
        print("\n✅ Database loaded successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
