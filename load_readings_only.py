#!/usr/bin/env python3
"""
Load only water level readings (wells already exist)
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

DATABASE_URL = "postgresql://groundwater_user:XCmOvmSsepDzDnCRRY9K08ALjA96JGwZ@dpg-dat0ojjncjis73cllkng-a.oregon-postgres.render.com/groundwater_l5m7"

print("=" * 60)
print("LOADING WATER LEVEL READINGS")
print("=" * 60)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Check wells count
cur.execute("SELECT COUNT(*) FROM wells")
total_wells = cur.fetchone()[0]
print(f"\n📍 Wells in database: {total_wells:,}")

# Get list of valid well IDs
cur.execute("SELECT well_id FROM wells")
valid_well_ids = set(row[0] for row in cur.fetchall())
print(f"   Valid well IDs loaded: {len(valid_well_ids)}")

# Load water levels CSV
print("\n💧 Loading water_levels.csv...")
water_levels_df = pd.read_csv("data/water_levels.csv")
print(f"   Found {len(water_levels_df):,} readings in CSV")
print(f"   Columns: {list(water_levels_df.columns)}")

# Prepare rows for insertion
rows = []
skipped_no_well = 0
skipped_bad_date = 0
skipped_no_value = 0

print("\n🔄 Processing readings...")
for idx, row in water_levels_df.iterrows():
    try:
        well_id = str(row['Well No']).strip()
        
        # Skip if well doesn't exist
        if well_id not in valid_well_ids:
            skipped_no_well += 1
            continue
        
        date_str = str(row['date'])
        
        # Parse date
        try:
            if '/' in date_str:
                date = datetime.strptime(date_str, '%m/%d/%Y')
            else:
                date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            skipped_bad_date += 1
            continue
        
        # Get water level values
        head_msl = row.get('head_msl_m')
        depth_bgl = row.get('Water Level')
        
        if pd.isna(head_msl) and pd.isna(depth_bgl):
            skipped_no_value += 1
            continue
        
        rows.append((
            well_id,
            date.date(),
            float(depth_bgl) if not pd.isna(depth_bgl) else None,
            float(head_msl) if not pd.isna(head_msl) else None,
            'csv_import'
        ))
        
        if len(rows) % 10000 == 0:
            print(f"   ✓ Prepared {len(rows):,} readings...")
            
    except Exception as e:
        continue

print(f"\n📊 Preparation complete:")
print(f"   Valid readings: {len(rows):,}")
print(f"   Skipped (no well): {skipped_no_well:,}")
print(f"   Skipped (bad date): {skipped_bad_date:,}")
print(f"   Skipped (no value): {skipped_no_value:,}")

# Insert in batches
print("\n💾 Inserting readings into database...")
insert_sql = """
    INSERT INTO readings (well_id, date, depth_bgl_m, head_msl_m, source)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (well_id, date) DO UPDATE SET
        depth_bgl_m = EXCLUDED.depth_bgl_m,
        head_msl_m = EXCLUDED.head_msl_m
"""

batch_size = 1000
inserted = 0

for i in range(0, len(rows), batch_size):
    batch = rows[i:i+batch_size]
    try:
        execute_batch(cur, insert_sql, batch, page_size=1000)
        conn.commit()
        inserted += len(batch)
        if inserted % 10000 == 0:
            print(f"   ✅ Inserted {inserted:,}/{len(rows):,} readings...")
    except Exception as e:
        print(f"   ⚠️ Error in batch: {e}")
        conn.rollback()
        continue

print(f"\n✅ Successfully inserted {inserted:,} water level readings!")

# Calculate trend labels
print("\n📈 Calculating trend labels...")
try:
    cur.execute("""
        WITH well_trends AS (
            SELECT 
                well_id,
                COUNT(*) as reading_count,
                REGR_SLOPE(head_msl_m, EXTRACT(EPOCH FROM date)) as slope
            FROM readings
            WHERE head_msl_m IS NOT NULL
            GROUP BY well_id
            HAVING COUNT(*) >= 12
        )
        UPDATE wells w
        SET trend_label = CASE
            WHEN t.slope >= -0.00000001 THEN 'Stable'
            WHEN t.slope >= -0.00000005 THEN 'Watch'
            ELSE 'Critical'
        END
        FROM well_trends t
        WHERE w.well_id = t.well_id
    """)
    
    updated = cur.rowcount
    conn.commit()
    print(f"   ✅ Updated trends for {updated} wells")
except Exception as e:
    print(f"   ⚠️ Error: {e}")

# Final statistics
print("\n" + "=" * 60)
print("FINAL STATISTICS")
print("=" * 60)

cur.execute("SELECT COUNT(*) FROM wells")
print(f"\n📍 Total wells: {cur.fetchone()[0]:,}")

cur.execute("SELECT COUNT(*) FROM readings")
total_readings = cur.fetchone()[0]
print(f"\n💧 Total readings: {total_readings:,}")

cur.execute("SELECT COUNT(DISTINCT well_id) FROM readings")
wells_with_data = cur.fetchone()[0]
print(f"   Wells with data: {wells_with_data}")

if wells_with_data > 0:
    print(f"   Avg per well: {total_readings//wells_with_data}")

cur.execute("SELECT MIN(date), MAX(date) FROM readings")
min_date, max_date = cur.fetchone()
if min_date and max_date:
    print(f"\n📅 Date range: {min_date} to {max_date}")

# Trend distribution
cur.execute("""
    SELECT trend_label, COUNT(*) 
    FROM wells 
    WHERE trend_label IS NOT NULL
    GROUP BY trend_label
    ORDER BY CASE trend_label
        WHEN 'Critical' THEN 1
        WHEN 'Watch' THEN 2
        WHEN 'Stable' THEN 3
    END
""")
print(f"\n📊 Trend distribution:")
for label, count in cur.fetchall():
    print(f"   {label:10} → {count} wells")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ READINGS LOADED SUCCESSFULLY!")
print("=" * 60)
print("\n🌐 Test the API:")
print("   https://mp-groundwater-backend-z6hh.onrender.com/api/v1/wells/PANNA104-OW/history")
print("\n📊 Should now return water level readings!")
print("=" * 60)
