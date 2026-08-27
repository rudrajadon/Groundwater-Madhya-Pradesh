#!/usr/bin/env python3
"""
Load Rainfall Data to PostgreSQL
==================================
Loads monthly rainfall data into PostgreSQL database.

Author: Rudra Pratap Singh Jadon
Date: 2025-08-27
"""

import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

DATA_FILE = 'data/rainfall_well_monthly.csv'
DB_CONFIG = {
    'dbname': 'groundwater',
    'user': 'gwuser',
    'password': 'changeme',
    'host': 'localhost',
    'port': 5432
}

print("=" * 70)
print("LOAD RAINFALL DATA TO POSTGRESQL")
print("=" * 70)

# Load data
print(f"\n[1/4] Loading data from {DATA_FILE}...")
df = pd.read_csv(DATA_FILE)
df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
print(f"  Records: {len(df):,}")

# Connect to database
print("\n[2/4] Connecting to PostgreSQL...")
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("  ✓ Connected")
except Exception as e:
    print(f"  ✗ Connection failed: {e}")
    print("  Note: Start database with: cd infra && docker-compose up -d db")
    sys.exit(1)

# Create table
print("\n[3/4] Creating rainfall table...")
cur.execute("""
    DROP TABLE IF EXISTS rainfall CASCADE;
    CREATE TABLE rainfall (
        id SERIAL PRIMARY KEY,
        well_id VARCHAR(50) NOT NULL,
        date DATE NOT NULL,
        rainfall_mm REAL,
        source VARCHAR(20) DEFAULT 'IMD_0.25deg',
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(well_id, date)
    );
    CREATE INDEX idx_rainfall_well_date ON rainfall(well_id, date);
    CREATE INDEX idx_rainfall_date ON rainfall(date);
""")
conn.commit()
print("  ✓ Table created with indexes")

# Insert data
print("\n[4/4] Inserting data...")
data = [(row['well_id'], row['date'], row['rainfall_mm']) 
        for _, row in df.iterrows()]
execute_values(cur, 
    "INSERT INTO rainfall (well_id, date, rainfall_mm) VALUES %s",
    data, page_size=1000)
conn.commit()
print(f"  ✓ Inserted {len(data):,} records")

# Verify
cur.execute("SELECT COUNT(*) FROM rainfall")
count = cur.fetchone()[0]
print(f"\n✓ Verification: {count:,} records in database")

cur.close()
conn.close()

print("\n" + "=" * 70)
print("✓ RAINFALL DATA LOADED SUCCESSFULLY")
print("=" * 70)
