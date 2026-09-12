#!/usr/bin/env python3
"""
Add the forecast_decline_m column to wells table
"""

import psycopg2

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

print("🔌 Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("📊 Adding forecast_decline_m column to wells table...")

try:
    cur.execute("""
        ALTER TABLE wells 
        ADD COLUMN IF NOT EXISTS forecast_decline_m NUMERIC
    """)
    conn.commit()
    print("✅ Column added successfully!")
except Exception as e:
    print(f"⚠️ Error: {e}")
    conn.rollback()

cur.close()
conn.close()

print("\n✅ Done! Now run use_real_local_trends.py again")
