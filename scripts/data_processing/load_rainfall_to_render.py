#!/usr/bin/env python3
"""
Load rainfall data to Render PostgreSQL database
Creates well_rainfall table and loads data from CSV
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

def main():
    print("=" * 70)
    print("LOADING RAINFALL DATA TO RENDER DATABASE")
    print("=" * 70)
    
    # Check if CSV exists
    csv_path = os.path.join(os.path.dirname(__file__), "data", "rainfall_well_monthly.csv")
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found!")
        return
    
    print(f"\n📂 Loading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} rainfall records from CSV")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Wells: {df['well_id'].nunique()}")
    print(f"   Year range: {df['year'].min()} - {df['year'].max()}")
    
    # Connect to database
    print(f"\n🔌 Connecting to Render database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✅ Connected!")
    
    # Create table if it doesn't exist
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
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_well_rainfall_date 
        ON well_rainfall(year, month)
    """)
    
    conn.commit()
    print("✅ Table created!")
    
    # Prepare data
    print(f"\n📝 Preparing {len(df)} records for insertion...")
    rows = []
    for _, row in df.iterrows():
        rows.append((
            str(row['well_id']),
            int(row['year']),
            int(row['month']),
            float(row['rainfall_mm'])
        ))
    
    print(f"✅ Prepared {len(rows)} records")
    
    # Batch insert
    print(f"\n🚀 Inserting records (batch size: 1000)...")
    execute_batch(cur, """
        INSERT INTO well_rainfall (well_id, year, month, rainfall_mm)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (well_id, year, month) DO UPDATE 
        SET rainfall_mm = EXCLUDED.rainfall_mm
    """, rows, page_size=1000)
    
    conn.commit()
    print(f"✅ Inserted {len(rows)} records!")
    
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
    print(f"✅ RAINFALL DATA LOADED SUCCESSFULLY!")
    print(f"{'='*70}")
    print(f"  Total records: {result[0]:,}")
    print(f"  Wells with data: {result[1]}")
    print(f"  Year range: {result[2]} - {result[3]}")
    print(f"{'='*70}")
    
    # Sample a well
    cur.execute("""
        SELECT well_id, COUNT(*) as months
        FROM well_rainfall
        GROUP BY well_id
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)
    sample = cur.fetchone()
    print(f"\n📌 Sample well: {sample[0]} has {sample[1]} months of rainfall data")
    
    cur.close()
    conn.close()
    
    print(f"\n🎉 Done! Rainfall data is now available in production!")

if __name__ == "__main__":
    main()
