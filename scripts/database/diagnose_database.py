#!/usr/bin/env python3
"""
Diagnose what's actually in the database
"""

import psycopg2

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("=" * 60)
print("DATABASE DIAGNOSIS")
print("=" * 60)

# Check wells count and trends
print("\n1. WELLS:")
cur.execute("SELECT COUNT(*) FROM wells")
print(f"   Total wells: {cur.fetchone()[0]}")

cur.execute("""
    SELECT trend_label, COUNT(*) 
    FROM wells 
    GROUP BY trend_label
""")
print("\n   Trends:")
for row in cur.fetchall():
    print(f"   {row[0] if row[0] else 'NULL':10} → {row[1]}")

# Check readings
print("\n2. READINGS:")
cur.execute("SELECT COUNT(*) FROM readings")
total_readings = cur.fetchone()[0]
print(f"   Total readings: {total_readings}")

cur.execute("SELECT COUNT(DISTINCT well_id) FROM readings")
wells_with_data = cur.fetchone()[0]
print(f"   Wells with readings: {wells_with_data}")

# Sample a well with readings
cur.execute("""
    SELECT r.well_id, COUNT(*) as reading_count
    FROM readings r
    JOIN wells w ON r.well_id = w.well_id
    GROUP BY r.well_id
    ORDER BY reading_count DESC
    LIMIT 1
""")
if cur.rowcount > 0:
    sample_well, count = cur.fetchone()
    print(f"\n3. SAMPLE WELL: {sample_well}")
    print(f"   Reading count: {count}")
    
    # Get well details
    cur.execute("""
        SELECT well_id, district, trend_label, geology_type, aquifer_zone
        FROM wells WHERE well_id = %s
    """, (sample_well,))
    well_data = cur.fetchone()
    print(f"   District: {well_data[1]}")
    print(f"   Trend: {well_data[2]}")
    print(f"   Geology: {well_data[3]}")
    print(f"   Aquifer: {well_data[4]}")
    
    # Get some readings
    cur.execute("""
        SELECT date, depth_bgl_m, head_msl_m
        FROM readings
        WHERE well_id = %s
        ORDER BY date DESC
        LIMIT 5
    """, (sample_well,))
    print(f"\n   Recent readings:")
    for row in cur.fetchall():
        print(f"   {row[0]} → depth: {row[1]}, head: {row[2]}")

# Check if head_msl_m is populated
print("\n4. DATA QUALITY:")
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN head_msl_m IS NOT NULL THEN 1 END) as with_head,
        COUNT(CASE WHEN depth_bgl_m IS NOT NULL THEN 1 END) as with_depth
    FROM readings
""")
total, with_head, with_depth = cur.fetchone()
print(f"   Total readings: {total}")
print(f"   With head_msl_m: {with_head} ({with_head*100//total if total else 0}%)")
print(f"   With depth_bgl_m: {with_depth} ({with_depth*100//total if total else 0}%)")

# Check trend calculation
print("\n5. TREND CALCULATION TEST:")
cur.execute("""
    SELECT 
        well_id,
        COUNT(*) as readings,
        MIN(head_msl_m) as min_head,
        MAX(head_msl_m) as max_head,
        AVG(head_msl_m) as avg_head
    FROM readings
    WHERE head_msl_m IS NOT NULL
    GROUP BY well_id
    HAVING COUNT(*) >= 12
    LIMIT 5
""")
print("   Sample wells with data for trend:")
for row in cur.fetchall():
    print(f"   {row[0]}: {row[1]} readings, range {row[2]:.2f}-{row[3]:.2f}, avg {row[4]:.2f}")

cur.close()
conn.close()

print("\n" + "=" * 60)
