#!/usr/bin/env python3
"""
Extract water level readings from Panna MDB files and load into database.
This will enable trend calculation (Stable/Watch/Critical) for Panna wells.
"""
import pandas as pd
import subprocess
import psycopg2
from io import StringIO
import re

def extract_mdb_water_levels(mdb_file, table_name="Water Levels"):
    """Extract water levels table from MDB file using mdb-export."""
    cmd = ['mdb-export', mdb_file, table_name]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    df = pd.read_csv(StringIO(result.stdout))
    return df

def standardize_well_id(well_id):
    """Standardize well ID: UPPERCASE, no spaces, 0W→OW."""
    if pd.isna(well_id):
        return well_id
    wid = str(well_id).strip().upper()
    wid = wid.replace(' ', '')
    wid = re.sub(r'-0W$', '-OW', wid)
    wid = re.sub(r'-0W-', '-OW-', wid)
    return wid

def extract_and_load():
    print("=" * 70)
    print("EXTRACTING PANNA WATER LEVEL READINGS")
    print("=" * 70)
    
    # 1. Extract from MDB
    print("\n1. Extracting from Spannaow.Mdb...")
    df = extract_mdb_water_levels('GW_Data/Water Level/Spannaow.Mdb')
    print(f"   Extracted {len(df)} records")
    print(f"   Columns: {list(df.columns)}")
    
    # 2. Standardize and clean
    print("\n2. Cleaning and standardizing data...")
    df['well_id'] = df['Well No'].apply(standardize_well_id)
    
    # Parse dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Extract water level (depth below ground level)
    df['depth_bgl_m'] = pd.to_numeric(df['Water Level'], errors='coerce')
    
    # Filter valid records
    df_clean = df[['well_id', 'date', 'depth_bgl_m']].dropna()
    
    print(f"   Cleaned records: {len(df_clean)}")
    print(f"   Date range: {df_clean['date'].min()} to {df_clean['date'].max()}")
    print(f"   Wells: {df_clean['well_id'].nunique()}")
    
    # 3. Get well coordinates and elevation from database
    print("\n3. Fetching well metadata from database...")
    conn = psycopg2.connect("postgresql://gwuser:changeme@localhost:5432/groundwater")
    cur = conn.cursor()
    
    cur.execute("""
        SELECT well_id, 
               ST_Y(geom::geometry) as latitude, 
               ST_X(geom::geometry) as longitude, 
               COALESCE(elevation_m, 0) as elevation_m 
        FROM wells 
        WHERE well_id LIKE 'PANNA%'
    """)
    wells_meta = pd.DataFrame(cur.fetchall(), columns=['well_id', 'latitude', 'longitude', 'elevation_m'])
    print(f"   Found metadata for {len(wells_meta)} Panna wells")
    
    # 4. Merge with well metadata
    print("\n4. Merging readings with well metadata...")
    df_merged = df_clean.merge(wells_meta, on='well_id', how='inner')
    print(f"   Merged records: {len(df_merged)}")
    
    # Convert elevation to float to match depth type
    df_merged['elevation_m'] = df_merged['elevation_m'].astype(float)
    
    # Calculate head (elevation - depth)
    df_merged['head_msl_m'] = df_merged['elevation_m'] - df_merged['depth_bgl_m']
    
    # 5. Check for existing Panna readings
    print("\n5. Checking for existing Panna readings...")
    cur.execute("SELECT COUNT(*) FROM readings WHERE well_id LIKE 'PANNA%'")
    existing_count = cur.fetchone()[0]
    print(f"   Existing Panna readings: {existing_count}")
    
    if existing_count > 0:
        print("   Deleting old Panna readings...")
        cur.execute("DELETE FROM readings WHERE well_id LIKE 'PANNA%'")
        print(f"   Deleted {cur.rowcount} old records")
    
    # 6. Insert new readings
    print("\n6. Inserting new readings into database...")
    inserted = 0
    
    for _, row in df_merged.iterrows():
        try:
            cur.execute("""
                INSERT INTO readings (well_id, date, depth_bgl_m, head_msl_m, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (well_id, date) DO NOTHING
            """, (
                row['well_id'],
                row['date'],
                row['depth_bgl_m'],
                row['head_msl_m'],
                'Spannaow.Mdb'
            ))
            inserted += 1
            
            if inserted % 1000 == 0:
                print(f"   Inserted {inserted}/{len(df_merged)} records...")
                
        except Exception as e:
            print(f"   ⚠️  Error inserting {row['well_id']}, {row['date']}: {e}")
            break  # Stop on first error to see what's wrong
    
    conn.commit()
    print(f"   ✓ Inserted {inserted} records")
    
    # 7. Verify and show sample
    print("\n7. Verification:")
    cur.execute("""
        SELECT w.well_id, COUNT(r.well_id) as reading_count,
               MIN(r.date) as earliest, MAX(r.date) as latest
        FROM wells w
        LEFT JOIN readings r ON w.well_id = r.well_id
        WHERE w.well_id LIKE 'PANNA%'
        GROUP BY w.well_id
        ORDER BY reading_count DESC
        LIMIT 10
    """)
    
    print(f"\n   {'Well ID':<20} {'Readings':<10} {'Earliest':<12} {'Latest'}")
    print("   " + "-" * 60)
    for well_id, count, earliest, latest in cur.fetchall():
        earliest_str = earliest.strftime('%Y-%m-%d') if earliest else 'N/A'
        latest_str = latest.strftime('%Y-%m-%d') if latest else 'N/A'
        print(f"   {well_id:<20} {count:<10} {earliest_str:<12} {latest_str}")
    
    # 8. Now recalculate trends
    print("\n8. Recalculating trend labels...")
    cur.execute("""
        WITH recent_trends AS (
            SELECT 
                well_id,
                MAX(head_msl_m) FILTER (WHERE date >= NOW() - INTERVAL '24 months' AND date < NOW() - INTERVAL '12 months') as prev_year_max,
                MAX(head_msl_m) FILTER (WHERE date >= NOW() - INTERVAL '12 months') as current_year_max
            FROM readings
            WHERE well_id LIKE 'PANNA%'
            GROUP BY well_id
        )
        UPDATE wells w
        SET trend_label = CASE
            WHEN t.prev_year_max IS NULL OR t.current_year_max IS NULL THEN 'Unknown'
            WHEN (t.prev_year_max - t.current_year_max) > 4.0 THEN 'Critical'
            WHEN (t.prev_year_max - t.current_year_max) BETWEEN 1.0 AND 4.0 THEN 'Watch'
            WHEN (t.prev_year_max - t.current_year_max) <= 1.0 THEN 'Stable'
            ELSE 'Unknown'
        END
        FROM recent_trends t
        WHERE w.well_id = t.well_id
    """)
    
    trend_updated = cur.rowcount
    conn.commit()
    print(f"   Updated trend labels for {trend_updated} wells")
    
    # 9. Show trend distribution
    cur.execute("""
        SELECT trend_label, COUNT(*) 
        FROM wells 
        WHERE well_id LIKE 'PANNA%' 
        GROUP BY trend_label
    """)
    
    print("\n9. Panna wells trend distribution:")
    for trend, count in cur.fetchall():
        print(f"   {trend:<12} {count} wells")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✓ PANNA WATER LEVELS EXTRACTED AND LOADED!")
    print("=" * 70)
    
    return inserted

if __name__ == "__main__":
    import sys
    try:
        inserted = extract_and_load()
        print(f"\n✅ Successfully loaded {inserted} water level records for Panna wells")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
