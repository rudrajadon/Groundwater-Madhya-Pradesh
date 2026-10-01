#!/usr/bin/env python3
"""
Add mock historical readings to wells so the forecast endpoint works
This creates realistic-looking water level trends for demo purposes
"""

import psycopg2
from datetime import datetime, timedelta
import random

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

print("🔌 Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Get all wells
cur.execute("SELECT well_id, trend_label FROM wells LIMIT 50")  # Start with 50 wells for speed
wells = cur.fetchall()
print(f"📊 Found {len(wells)} wells to add readings for")

# Generate 24 months of historical data (required by model)
end_date = datetime(2024, 12, 31)
dates = [end_date - timedelta(days=30*i) for i in range(24)]
dates.reverse()

print("\n📈 Generating mock readings...")
total_inserted = 0

for well_id, trend_label in wells:
    # Base water level (in meters above sea level)
    base_level = 450 + random.uniform(-50, 50)
    
    # Trend characteristics
    if trend_label == 'Stable':
        trend_decline = random.uniform(-0.5, 0.5)  # Minimal change
        noise = 2
    elif trend_label == 'Watch':
        trend_decline = random.uniform(0.5, 1.5)  # Moderate decline
        noise = 3
    elif trend_label == 'Critical':
        trend_decline = random.uniform(1.5, 3.0)  # Significant decline
        noise = 4
    else:  # Unknown
        trend_decline = 0
        noise = 2
    
    # Generate readings with seasonal variation
    readings = []
    for i, date in enumerate(dates):
        # Linear trend
        level = base_level - (trend_decline * i / 12)
        
        # Add seasonal variation (monsoon effect)
        month = date.month
        if 6 <= month <= 9:  # Monsoon months
            level += random.uniform(2, 5)
        elif month in [3, 4, 5]:  # Summer months
            level -= random.uniform(1, 3)
        
        # Add random noise
        level += random.uniform(-noise, noise)
        
        readings.append((well_id, date.date(), level))
    
    # Insert readings
    try:
        cur.executemany("""
            INSERT INTO readings (well_id, date, head_msl_m, source)
            VALUES (%s, %s, %s, 'mock_demo')
            ON CONFLICT (well_id, date) DO NOTHING
        """, readings)
        total_inserted += len(readings)
        
        if (wells.index((well_id, trend_label)) + 1) % 10 == 0:
            print(f"  ✅ {wells.index((well_id, trend_label)) + 1}/{len(wells)} wells processed...")
            conn.commit()
    except Exception as e:
        print(f"  ⚠️ Error for {well_id}: {e}")
        conn.rollback()

conn.commit()
print(f"\n✅ Inserted {total_inserted} mock readings for {len(wells)} wells")

# Verify
cur.execute("SELECT COUNT(DISTINCT well_id) FROM readings WHERE source = 'mock_demo'")
wells_with_data = cur.fetchone()[0]
print(f"📊 {wells_with_data} wells now have historical data")

cur.close()
conn.close()

print("\n🎉 Done! Wells now have mock readings for forecasting!")
print("\n🧪 Test by clicking a well on the map - forecast should work!")
print("🌐 https://groundwater-madhya-pradesh.vercel.app/")
