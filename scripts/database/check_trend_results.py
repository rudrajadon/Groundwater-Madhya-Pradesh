#!/usr/bin/env python3
"""
Check the final trend distribution after ML calculation
"""

import psycopg2

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

print("🔌 Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("\n" + "=" * 60)
print("FINAL TREND DISTRIBUTION (ML MODEL CALCULATED)")
print("=" * 60)

cur.execute("""
    SELECT 
        trend_label,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
    FROM wells
    WHERE trend_label IS NOT NULL
    GROUP BY trend_label
    ORDER BY 
        CASE trend_label
            WHEN 'Critical' THEN 1
            WHEN 'Watch' THEN 2
            WHEN 'Stable' THEN 3
            WHEN 'Unknown' THEN 4
        END
""")

print("\n📊 Trend Distribution:")
for row in cur.fetchall():
    label, count, pct = row
    print(f"   {label:10} → {count:4} wells ({pct:5.1f}%)")

# Show sample wells from each category
print("\n" + "=" * 60)
print("SAMPLE WELLS FROM EACH CATEGORY")
print("=" * 60)

for trend in ['Critical', 'Watch', 'Stable']:
    print(f"\n🔍 {trend} Wells (sample):")
    cur.execute("""
        SELECT w.well_id, w.district, w.forecast_decline_m
        FROM wells w
        WHERE w.trend_label = %s AND w.forecast_decline_m IS NOT NULL
        ORDER BY w.forecast_decline_m
        LIMIT 5
    """, (trend,))
    
    for row in cur.fetchall():
        well_id, district, decline = row
        print(f"   {well_id:15} {district:15} → {decline:+7.2f}m decline")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ REFRESH YOUR APP NOW!")
print("🌐 https://groundwater-madhya-pradesh.vercel.app/")
print("=" * 60)
