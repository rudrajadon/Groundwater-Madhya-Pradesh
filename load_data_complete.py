#!/usr/bin/env python3
"""
Complete data loading script - loads wells FIRST, then readings
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

DATABASE_URL = "postgresql://groundwater_user:XCmOvmSsepDzDnCRRY9K08ALjA96JGwZ@dpg-dat0ojjncjis73cllkng-a.oregon-postgres.render.com/groundwater_l5m7"

print("=" * 60)
print("LOADING COMPLETE DATA TO RENDER")
print("=" * 60)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# ============================================================================
# STEP 1: Load WELLS first (required for foreign keys!)
# ============================================================================
print("\n📍 Step 1: Loading wells...")

try:
    wells_df = pd.read_csv("data/wells.csv")
    print(f"   Found {len(wells_df)} wells in CSV")
    print(f"   Columns: {list(wells_df.columns)}")
    
    wells_inserted = 0
    
    for _, row in wells_df.iterrows():
        try:
            well_id = str(row['Well No']).strip()
            
            # Wells.csv uses Northing/Easting (which are actually lat/lon)
            lat = row.get('Northing')
            lon = row.get('Easting')
            
            # Get geology from wells.csv directly (columns exist there too!)
            geology_type = row.get('geology_type')
            aquifer_class = row.get('aquifer_classification')
            
            # Create geography point if we have coords
            if pd.notna(lat) and pd.notna(lon):
                geom_sql = f"ST_GeogFromText('POINT({lon} {lat})')"
            else:
                geom_sql = "NULL"
            
            cur.execute(f"""
                INSERT INTO wells (
                    well_id, well_type, district, tahsil, block, village,
                    geom, lat_raw, lon_raw, elevation_m, aquifer_zone,
                    geology_type, aquifer_classification, trend_label
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    {geom_sql}, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (well_id) DO UPDATE SET
                    well_type = EXCLUDED.well_type,
                    district = EXCLUDED.district,
                    block = EXCLUDED.block,
                    aquifer_zone = EXCLUDED.aquifer_zone,
                    geology_type = EXCLUDED.geology_type,
                    aquifer_classification = EXCLUDED.aquifer_classification
            """, (
                well_id,
                row.get('Well Type'),
                row.get('District'),
                row.get('Tahsil / Taluk'),
                row.get('Block / Mandal'),
                row.get('Village'),
                str(lat) if pd.notna(lat) else None,
                str(lon) if pd.notna(lon) else None,
                row.get('Elevation of Ground Level'),
                row.get('Aquifer Zone'),
                geology_type if pd.notna(geology_type) else None,
                aquifer_class if pd.notna(aquifer_class) else None,
                'Stable'  # Default, will calculate later
            ))
            
            wells_inserted += 1
            
            if wells_inserted % 100 == 0:
                print(f"   Inserted {wells_inserted} wells...")
                conn.commit()
                
        except Exception as e:
            print(f"   ⚠️ Error inserting well {row.get('Well No')}: {e}")
            continue
    
    conn.commit()
    print(f"   ✅ Inserted {wells_inserted} wells!")
    
except Exception as e:
    print(f"   ❌ Error loading wells: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ============================================================================
# STEP 2: Load READINGS (now that wells exist!)
# ============================================================================
print("\n💧 Step 2: Loading water level readings...")

try:
    water_levels_df = pd.read_csv("data/water_levels.csv")
    print(f"   Found {len(water_levels_df)} readings in CSV")
    
    # Get list of valid well IDs from database
    cur.execute("SELECT well_id FROM wells")
    valid_well_ids = set(row[0] for row in cur.fetchall())
    print(f"   Have {len(valid_well_ids)} wells in database")
    
    rows = []
    skipped_no_well = 0
    skipped_bad_date = 0
    skipped_no_value = 0
    
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
                print(f"   Prepared {len(rows)} readings...")
                
        except Exception as e:
            continue
    
    print(f"\n   📊 Prepared {len(rows)} valid readings")
    print(f"      Skipped: {skipped_no_well} (no well), {skipped_bad_date} (bad date), {skipped_no_value} (no value)")
    
    # Insert in batches
    print("\n   💾 Inserting readings...")
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
                print(f"      ✅ Inserted {inserted:,}/{len(rows):,} readings...")
        except Exception as e:
            print(f"      ⚠️ Error in batch: {e}")
            conn.rollback()
            continue
    
    print(f"   ✅ Successfully inserted {inserted:,} water level readings!")
    
except Exception as e:
    print(f"   ❌ Error loading readings: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# STEP 3: Calculate trend labels from actual data
# ============================================================================
print("\n📈 Step 3: Calculating trend labels...")

try:
    cur.execute("""
        WITH well_trends AS (
            SELECT 
                well_id,
                COUNT(*) as reading_count,
                -- Calculate linear trend (negative = declining)
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
    print(f"   ✅ Calculated trends for {updated} wells")
    
except Exception as e:
    print(f"   ⚠️ Error calculating trends: {e}")

# ============================================================================
# FINAL STATISTICS
# ============================================================================
print("\n" + "=" * 60)
print("DATABASE STATISTICS")
print("=" * 60)

cur.execute("SELECT COUNT(*) FROM wells")
total_wells = cur.fetchone()[0]
print(f"\n📍 Wells: {total_wells:,}")

cur.execute("SELECT COUNT(*) FROM readings")
total_readings = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT well_id) FROM readings")
wells_with_readings = cur.fetchone()[0]
print(f"\n💧 Readings: {total_readings:,}")
print(f"   Wells with data: {wells_with_readings}")
if wells_with_readings > 0:
    print(f"   Avg per well: {total_readings//wells_with_readings}")

# Date range
cur.execute("SELECT MIN(date), MAX(date) FROM readings")
min_date, max_date = cur.fetchone()
print(f"\n📅 Date range: {min_date} to {max_date}")

# Trends
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
print(f"\n📊 Trends:")
for row in cur.fetchall():
    print(f"   {row[0]:10} → {row[1]} wells")

# Top districts
cur.execute("""
    SELECT district, COUNT(*) 
    FROM wells 
    WHERE district IS NOT NULL
    GROUP BY district
    ORDER BY COUNT(*) DESC
    LIMIT 10
""")
print(f"\n🗺️ Top Districts:")
for row in cur.fetchall():
    print(f"   {row[0]:20} → {row[1]} wells")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ DATA LOADING COMPLETE!")
print("=" * 60)
print("\n🌐 Test your backend:")
print("   https://mp-groundwater-backend-z6hh.onrender.com/api/v1/wells")
print("\n📊 Should now return REAL wells with data!")
print("=" * 60)
