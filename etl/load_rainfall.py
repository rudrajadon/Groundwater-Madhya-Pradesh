#!/usr/bin/env python3
"""Load monthly rainfall data for each well."""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import os

DATABASE_URL = "postgresql://gwuser:changeme@localhost:5432/groundwater"

def main():
    print("Loading rainfall data...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "rainfall_well_monthly.csv")
    
    df = pd.read_csv(data_path)
    print(f"  Loaded {len(df)} rainfall records from CSV")
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Prepare data
    rows = []
    for _, row in df.iterrows():
        rows.append((
            row['well_id'],
            int(row['year']),
            int(row['month']),
            float(row['rainfall_mm'])
        ))
    
    print(f"  Inserting {len(rows)} records...")
    
    # Batch insert for performance
    execute_batch(cur, """
        INSERT INTO well_rainfall (well_id, year, month, rainfall_mm)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (well_id, year, month) DO UPDATE 
        SET rainfall_mm = EXCLUDED.rainfall_mm
    """, rows, page_size=1000)
    
    conn.commit()
    print(f"✓ Inserted {len(rows)} rainfall records")
    
    # Verify
    cur.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT well_id) as total_wells,
            MIN(year) as min_year,
            MAX(year) as max_year
        FROM well_rainfall
    """)
    
    result = cur.fetchone()
    print(f"\n✅ Rainfall data loaded:")
    print(f"  Total records: {result[0]:,}")
    print(f"  Wells with data: {result[1]}")
    print(f"  Year range: {result[2]} - {result[3]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
