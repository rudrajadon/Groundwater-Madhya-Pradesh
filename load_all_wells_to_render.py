#!/usr/bin/env python3
"""
Load ALL wells from data/wells.csv to Render PostgreSQL database
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import sys

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

print("📂 Reading wells.csv...")
df = pd.read_csv("data/wells.csv")
print(f"✅ Found {len(df)} wells in CSV")

print("\n🔌 Connecting to Render database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("📊 Preparing data...")
rows = []
skipped = 0

for idx, r in df.iterrows():
    try:
        well_id = str(r["Well No"]).strip()
        
        # Skip if no well ID
        if not well_id or well_id == 'nan':
            skipped += 1
            continue
        
        # Get coordinates
        lat = r.get("Northing")
        lon = r.get("Easting")
        
        # Skip if no coordinates
        if pd.isna(lat) or pd.isna(lon):
            skipped += 1
            continue
        
        # Prepare row
        row = (
            well_id,
            r.get("Well Type"),
            r.get("District"),
            r.get("Tahsil / Taluk"),
            r.get("Block / Mandal"),
            r.get("Village"),
            float(lon),
            float(lat),
            str(lat) if not pd.isna(lat) else None,
            str(lon) if not pd.isna(lon) else None,
            bool(r.get("Coord Validated", False)),
            float(r["Elevation of Ground Level"]) if not pd.isna(r.get("Elevation of Ground Level")) else None,
            r.get("Aquifer Zone"),
            float(r["Command Area"]) if not pd.isna(r.get("Command Area")) else None,
            r.get("geology_type"),
            r.get("aquifer_classification"),
            r.get("trend_label")
        )
        rows.append(row)
        
        if len(rows) % 100 == 0:
            print(f"  Prepared {len(rows)} wells...")
            
    except Exception as e:
        print(f"  ⚠️ Skipped row {idx}: {e}")
        skipped += 1
        continue

print(f"\n✅ Prepared {len(rows)} wells (skipped {skipped})")

print("\n💾 Inserting wells into database...")
insert_sql = """
    INSERT INTO wells (
        well_id, well_type, district, tahsil, block, village,
        geom, lat_raw, lon_raw, coord_validated,
        elevation_m, aquifer_zone, command_area,
        geology_type, aquifer_classification, trend_label
    ) VALUES (
        %s, %s, %s, %s, %s, %s,
        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
        %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (well_id) DO UPDATE SET
        well_type = EXCLUDED.well_type,
        district = EXCLUDED.district,
        tahsil = EXCLUDED.tahsil,
        block = EXCLUDED.block,
        village = EXCLUDED.village,
        geom = EXCLUDED.geom,
        lat_raw = EXCLUDED.lat_raw,
        lon_raw = EXCLUDED.lon_raw,
        coord_validated = EXCLUDED.coord_validated,
        elevation_m = EXCLUDED.elevation_m,
        aquifer_zone = EXCLUDED.aquifer_zone,
        command_area = EXCLUDED.command_area,
        geology_type = EXCLUDED.geology_type,
        aquifer_classification = EXCLUDED.aquifer_classification,
        trend_label = EXCLUDED.trend_label
"""

# Insert in batches for better performance
batch_size = 100
inserted = 0

for i in range(0, len(rows), batch_size):
    batch = rows[i:i+batch_size]
    try:
        execute_batch(cur, insert_sql, batch, page_size=100)
        conn.commit()
        inserted += len(batch)
        print(f"  ✅ Inserted {inserted}/{len(rows)} wells...")
    except Exception as e:
        print(f"  ⚠️ Error inserting batch at {i}: {e}")
        conn.rollback()
        # Try one by one for this batch
        for row in batch:
            try:
                cur.execute(insert_sql, row)
                conn.commit()
                inserted += 1
            except Exception as e2:
                print(f"    ⚠️ Skipped well {row[0]}: {e2}")
                conn.rollback()

print(f"\n✅ Successfully inserted {inserted} wells!")

# Get final statistics
print("\n📊 Database Statistics:")

cur.execute("SELECT COUNT(*) FROM wells")
total = cur.fetchone()[0]
print(f"  Total wells: {total}")

cur.execute("""
    SELECT district, COUNT(*) as count
    FROM wells
    WHERE district IS NOT NULL
    GROUP BY district
    ORDER BY count DESC
    LIMIT 10
""")
print("\n  Top 10 districts by well count:")
for row in cur.fetchall():
    print(f"    {row[0]:20} → {row[1]:4} wells")

cur.execute("""
    SELECT 
        COUNT(CASE WHEN trend_label = 'Stable' THEN 1 END) as stable,
        COUNT(CASE WHEN trend_label = 'Watch' THEN 1 END) as watch,
        COUNT(CASE WHEN trend_label = 'Critical' THEN 1 END) as critical,
        COUNT(CASE WHEN trend_label IS NULL THEN 1 END) as unknown
    FROM wells
""")
stats = cur.fetchone()
print(f"\n  Trend distribution:")
print(f"    Stable:   {stats[0]:4} wells")
print(f"    Watch:    {stats[1]:4} wells")
print(f"    Critical: {stats[2]:4} wells")
print(f"    Unknown:  {stats[3]:4} wells")

cur.close()
conn.close()

print("\n🎉 Done! All wells loaded to Render database!")
print("\n🌐 Refresh your frontend:")
print("   https://groundwater-madhya-pradesh.vercel.app/")
print("\n🧪 Test API:")
print("   https://mp-groundwater-backend.onrender.com/api/v1/wells")
