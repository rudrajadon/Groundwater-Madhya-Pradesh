#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://groundwater_user:XCmOvmSsepDzDnCRRY9K08ALjA96JGwZ@dpg-dat0ojjncjis73cllkng-a.oregon-postgres.render.com/groundwater_l5m7"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Check if forecast_cache column exists
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'wells' AND column_name LIKE '%forecast%'
""")
print("Forecast-related columns in wells table:")
for row in cur.fetchall():
    print(f"  {row['column_name']}: {row['data_type']}")

# Check TKM008-OW data
cur.execute("""
    SELECT well_id, forecast_cache, forecast_decline_m, trend_label
    FROM wells 
    WHERE well_id = 'TKM008-OW'
""")
row = cur.fetchone()
print(f"\nTKM008-OW data:")
print(f"  trend_label: {row['trend_label']}")
print(f"  forecast_decline_m: {row['forecast_decline_m']}")
print(f"  forecast_cache: {row['forecast_cache']}")

cur.close()
conn.close()
