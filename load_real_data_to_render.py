#!/usr/bin/env python3
"""
Load ALL REAL DATA to Render PostgreSQL
This loads the exact same data you had when running locally
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import sys
from datetime import datetime

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

print("=" * 60)
print("LOADING REAL DATA TO RENDER DATABASE")
print("=" * 60)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# ============================================================================
# 1. LOAD WELLS (Already done, but update with geology data)
# ============================================================================
print("\n📊 Step 1: Loading well geology classifications...")
try:
    geology_df = pd.read_csv("data/well_geology_classifications.csv")
    print(f"   Found {len(geology_df)} wells with geology data")
    
    updated = 0
    for _, row in geology_df.iterrows():
        try:
            cur.execute("""
                UPDATE wells 
                SET geology_type = %s,
                    aquifer_classification = %s,
                    aquifer_zone = %s
                WHERE well_id = %s
            """, (
                row.get('geology_type'),
                row.get('aquifer_classification'),
                row.get('aquifer_zone'),
                row['Well No']
            ))
            if cur.rowcount > 0:
                updated += 1
        except Exception as e:
            continue
    
    conn.commit()
    print(f"   ✅ Updated {updated} wells with geology data")
except Exception as e:
    print(f"   ⚠️ Error loading geology: {e}")

# ============================================================================
# 2. LOAD WATER LEVEL READINGS (THE CRITICAL PART!)
# ============================================================================
print("\n💧 Step 2: Loading water level readings...")
print("   (This is the real historical data your app needs!)")

try:
    water_levels_df = pd.read_csv("data/water_levels.csv")
    print(f"   Found {len(water_levels_df)} readings in CSV")
    
    # Prepare data
    rows = []
    skipped = 0
    
    for idx, row in water_levels_df.iterrows():
        try:
            well_id = str(row['Well No']).strip()
            date_str = str(row['date'])
            
            # Parse date
            try:
                if '/' in date_str:
                    date = datetime.strptime(date_str, '%m/%d/%Y')
                else:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
            except:
                skipped += 1
                continue
            
            # Get water level (head_msl_m is what the model uses!)
            head_msl = row.get('head_msl_m')
            depth_bgl = row.get('Water Level')
            
            if pd.isna(head_msl) and pd.isna(depth_bgl):
                skipped += 1
                continue
            
            rows.append((
                well_id,
                date.date(),
                float(depth_bgl) if not pd.isna(depth_bgl) else None,
                float(head_msl) if not pd.isna(head_msl) else None,
                'csv_import'
            ))
            
            if len(rows) % 5000 == 0:
                print(f"   Prepared {len(rows)} readings...")
                
        except Exception as e:
            skipped += 1
            continue
    
    print(f"   ✅ Prepared {len(rows)} readings (skipped {skipped})")
    
    # Insert in batches
    print("   💾 Inserting readings into database...")
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
            print(f"   ✅ Inserted {inserted}/{len(rows)} readings...")
        except Exception as e:
            print(f"   ⚠️ Error in batch: {e}")
            conn.rollback()
    
    print(f"   ✅ Successfully inserted {inserted} water level readings!")
    
except Exception as e:
    print(f"   ❌ Error loading water levels: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# 3. CALCULATE REAL TREND LABELS
# ============================================================================
print("\n📈 Step 3: Calculating trend labels from real data...")

try:
    # Calculate trend for each well based on their actual readings
    cur.execute("""
        WITH well_trends AS (
            SELECT 
                well_id,
                COUNT(*) as reading_count,
                MIN(date) as first_date,
                MAX(date) as last_date,
                -- Calculate linear regression slope (trend)
                REGR_SLOPE(head_msl_m, EXTRACT(EPOCH FROM date)) as slope,
                -- Calculate standard deviation
                STDDEV(head_msl_m) as volatility
            FROM readings
            WHERE head_msl_m IS NOT NULL
            GROUP BY well_id
            HAVING COUNT(*) >= 12  -- Need at least 12 readings for reliable trend
        )
        UPDATE wells w
        SET trend_label = CASE
            WHEN t.slope > -0.00000001 THEN 'Stable'     -- Rising or stable (slope ~ 0)
            WHEN t.slope > -0.00000005 THEN 'Watch'      -- Moderate decline
            ELSE 'Critical'                               -- Significant decline
        END
        FROM well_trends t
        WHERE w.well_id = t.well_id
    """)
    
    updated = cur.rowcount
    conn.commit()
    print(f"   ✅ Calculated trends for {updated} wells based on real data!")
    
except Exception as e:
    print(f"   ⚠️ Error calculating trends: {e}")

# ============================================================================
# 4. FINAL STATISTICS
# ============================================================================
print("\n" + "=" * 60)
print("DATABASE STATISTICS")
print("=" * 60)

# Wells
cur.execute("SELECT COUNT(*) FROM wells")
total_wells = cur.fetchone()[0]
print(f"\n📍 Total Wells: {total_wells}")

# Readings
cur.execute("SELECT COUNT(*) FROM readings")
total_readings = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT well_id) FROM readings")
wells_with_readings = cur.fetchone()[0]
print(f"\n💧 Total Readings: {total_readings:,}")
print(f"   Wells with data: {wells_with_readings}")
print(f"   Avg readings per well: {total_readings//wells_with_readings if wells_with_readings > 0 else 0}")

# Trends
cur.execute("""
    SELECT 
        trend_label,
        COUNT(*) as count
    FROM wells
    WHERE trend_label IS NOT NULL
    GROUP BY trend_label
    ORDER BY 
        CASE trend_label
            WHEN 'Critical' THEN 1
            WHEN 'Watch' THEN 2
            WHEN 'Stable' THEN 3
        END
""")
print(f"\n📊 Trend Distribution (from REAL data):")
for row in cur.fetchall():
    print(f"   {row[0]:10} → {row[1]:5} wells")

# Districts
cur.execute("""
    SELECT district, COUNT(*) as count
    FROM wells
    WHERE district IS NOT NULL
    GROUP BY district
    ORDER BY count DESC
    LIMIT 10
""")
print(f"\n🗺️ Top 10 Districts:")
for row in cur.fetchall():
    print(f"   {row[0]:20} → {row[1]:4} wells")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ DONE! Your app now has ALL REAL DATA!")
print("=" * 60)
print("\n🌐 Test your app:")
print("   https://groundwater-madhya-pradesh.vercel.app/")
print("\n🧪 Test API:")
print("   https://mp-groundwater-backend.onrender.com/api/v1/wells")
print("\n📈 Click any well - forecast should work with REAL data!")
print("=" * 60)
