#!/usr/bin/env python3
"""
Fix wells with 'Unknown' district by mapping them based on their coordinates
"""

import psycopg2

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

print("🔌 Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Check how many wells have Unknown district
cur.execute("""
    SELECT 
        COUNT(*) FILTER (WHERE district = 'Unknown' OR district IS NULL OR district = '') as unknown_count,
        COUNT(*) as total
    FROM wells
""")
unknown, total = cur.fetchone()
print(f"📊 Wells with Unknown/NULL district: {unknown} / {total}")

if unknown == 0:
    print("✅ All wells have districts assigned!")
    cur.close()
    conn.close()
    exit(0)

# Map districts based on well ID prefixes (from your MDB files)
print(f"\n🗺️  Mapping districts based on well ID patterns...")

district_mappings = {
    'BPL': 'Bhopal',
    'SUJN': 'Ujjain',
    'SIND': 'Indore',
    'SGWL': 'Gwalior',
    'SGUN': 'Guna',
    'SGR': 'Sagar',
    'SJBP': 'Jabalpur',
    'STN': 'Satna',
    'CHHAT': 'Chhatarpur',
    'TKM': 'Tikamgarh',
    'PANNA': 'Panna',
    'IND': 'Indore',
    'UJN': 'Ujjain',
    'JBP': 'Jabalpur',
}

updated = 0
for prefix, district in district_mappings.items():
    cur.execute("""
        UPDATE wells
        SET district = %s
        WHERE (district = 'Unknown' OR district IS NULL OR district = '')
        AND well_id LIKE %s
    """, (district, f'{prefix}%'))
    
    count = cur.rowcount
    if count > 0:
        updated += count
        print(f"  ✅ {district:15} → {count:4} wells")

conn.commit()

print(f"\n✅ Updated {updated} wells with district names")

# Show final statistics
cur.execute("""
    SELECT district, COUNT(*) as count
    FROM wells
    WHERE district IS NOT NULL AND district != '' AND district != 'Unknown'
    GROUP BY district
    ORDER BY count DESC
""")

print("\n📊 District distribution:")
for district, count in cur.fetchall():
    print(f"  {district:20} → {count:4} wells")

cur.close()
conn.close()

print("\n🎉 Done! Stress map should work now!")
