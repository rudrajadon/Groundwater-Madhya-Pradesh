#!/usr/bin/env python3
"""
Load RECENT rainfall data only (2015-2024, last 10 years) for production.
This keeps the database size manageable while showing rainfall in well details.
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

def main():
    print("=" * 70)
    print("LOADING RECENT RAINFALL DATA (2015-2024 - LAST 10 YEARS)")
    print("=" * 70)
    
    # Load CSV
    csv_path = os.path.join(os.path.dirname(__file__), "data", "rainfall_well_monthly.csv")
    print(f"\n📂 Loading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ Total records in CSV: {len(df):,}")
    
    # Filter to last 10 years (2015-2024)
    df_recent = df[df['year'] >= 2015].copy()
    print(f"✅ Filtered to 2015-2024: {len(df_recent):,} records")
    print(f"   Wells: {df_recent['well_id'].nunique()}")
    print(f"   Year range: {df_recent['year'].min()} - {df_recent['year'].max()}")
    
    # Connect to database
    print(f"\n🔌 Connecting to Render database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✅ Connected!")
    
    # Create table
    print("\n📊 Creating well_rainfall table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS well_rainfall (
            id SERIAL PRIMARY KEY,
            well_id VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            rainfall_mm NUMERIC NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(well_id, year, month)
        )
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_well_rainfall_well_id 
        ON well_rainfall(well_id)
    """)
    
    conn.commit()
    print("✅ Table created!")
    
    # Prepare data
    print(f"\n📝 Preparing {len(df_recent)} records...")
    rows = []
    for _, row in df_recent.iterrows():
        rows.append((
            str(row['well_id']),
            int(row['year']),
            int(row['month']),
            float(row['rainfall_mm'])
        ))
    
    # Batch insert
    print(f"\n🚀 Inserting {len(rows):,} records...")
    execute_batch(cur, """
        INSERT INTO well_rainfall (well_id, year, month, rainfall_mm)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (well_id, year, month) DO UPDATE 
        SET rainfall_mm = EXCLUDED.rainfall_mm
    """, rows, page_size=1000)
    
    conn.commit()
    print(f"✅ Inserted {len(rows):,} records!")
    
    # Verify
    print("\n📊 Verifying data...")
    cur.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT well_id) as total_wells,
            MIN(year) as min_year,
            MAX(year) as max_year
        FROM well_rainfall
    """)
    
    result = cur.fetchone()
    print(f"\n{'='*70}")
    print(f"✅ RAINFALL DATA LOADED!")
    print(f"{'='*70}")
    print(f"  Total records: {result[0]:,}")
    print(f"  Wells with data: {result[1]}")
    print(f"  Year range: {result[2]} - {result[3]}")
    print(f"{'='*70}")
    
    # Sample query
    cur.execute("""
        SELECT well_id, year, month, rainfall_mm
        FROM well_rainfall
        WHERE well_id = 'BPL001-OW'
        ORDER BY year DESC, month DESC
        LIMIT 5
    """)
    
    print(f"\n📌 Sample data for BPL001-OW (last 5 months):")
    for row in cur.fetchall():
        print(f"   {row[0]} - {row[1]}/{row[2]:02d}: {row[3]:.1f}mm")
    
    cur.close()
    conn.close()
    
    print(f"\n🎉 Done! Rainfall charts will now show in well details!")

if __name__ == "__main__":
    main()
