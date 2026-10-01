#!/usr/bin/env python3
"""
Add missing forecast columns to wells table
"""

import psycopg2

DATABASE_URL = "postgresql://groundwater_user:XCmOvmSsepDzDnCRRY9K08ALjA96JGwZ@dpg-dat0ojjncjis73cllkng-a.oregon-postgres.render.com/groundwater_l5m7"

print("=" * 60)
print("ADDING FORECAST COLUMNS TO WELLS TABLE")
print("=" * 60)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("\n✅ Connected to database")

# Add forecast_cache column (JSONB for storing cached forecasts)
print("\n📊 Adding forecast_cache column...")
try:
    cur.execute("""
        ALTER TABLE wells 
        ADD COLUMN IF NOT EXISTS forecast_cache JSONB;
    """)
    conn.commit()
    print("   ✅ forecast_cache column added")
except Exception as e:
    print(f"   ⚠️ Error: {e}")
    conn.rollback()

# Add forecast_decline_m column (NUMERIC for storing predicted decline)
print("\n📊 Adding forecast_decline_m column...")
try:
    cur.execute("""
        ALTER TABLE wells 
        ADD COLUMN IF NOT EXISTS forecast_decline_m NUMERIC;
    """)
    conn.commit()
    print("   ✅ forecast_decline_m column added")
except Exception as e:
    print(f"   ⚠️ Error: {e}")
    conn.rollback()

# Verify columns exist
print("\n📋 Verifying columns...")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'wells' 
    AND column_name IN ('forecast_cache', 'forecast_decline_m')
    ORDER BY column_name;
""")

columns = cur.fetchall()
print(f"\n✅ Found {len(columns)} forecast columns:")
for col in columns:
    print(f"   - {col[0]}: {col[1]}")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ FORECAST COLUMNS ADDED SUCCESSFULLY!")
print("=" * 60)
