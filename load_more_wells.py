#!/usr/bin/env python3
"""
Load more sample wells across Madhya Pradesh
This creates a better demo with wells distributed across the state
"""

import psycopg2
import random

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

# Major cities and towns in Madhya Pradesh with approximate coordinates
locations = [
    # District, Block, Lat, Lon
    ("Indore", "Indore", 22.7196, 75.8577),
    ("Indore", "Mhow", 22.5469, 75.7607),
    ("Indore", "Depalpur", 22.8508, 75.5426),
    ("Indore", "Sanwer", 22.9675, 75.8431),
    ("Bhopal", "Bhopal", 23.2599, 77.4126),
    ("Bhopal", "Berasia", 23.6333, 77.4333),
    ("Bhopal", "Huzur", 23.2594, 77.4126),
    ("Ujjain", "Ujjain", 23.1765, 75.7885),
    ("Ujjain", "Mahidpur", 23.4905, 75.6654),
    ("Ujjain", "Tarana", 23.3333, 76.0333),
    ("Jabalpur", "Jabalpur", 23.1815, 79.9864),
    ("Jabalpur", "Sihora", 23.4875, 80.1037),
    ("Jabalpur", "Patan", 23.2964, 79.6855),
    ("Gwalior", "Gwalior", 26.2183, 78.1828),
    ("Gwalior", "Dabra", 25.8856, 78.3321),
    ("Gwalior", "Bhitarwar", 25.7917, 78.1167),
    ("Sagar", "Sagar", 23.8388, 78.7378),
    ("Sagar", "Banda", 24.0454, 78.9618),
    ("Sagar", "Rehli", 23.6333, 79.0833),
    ("Satna", "Satna", 24.6005, 80.8322),
    ("Satna", "Maihar", 24.2655, 80.7593),
    ("Satna", "Nagod", 24.5667, 80.5833),
    ("Rewa", "Rewa", 24.5364, 81.2961),
    ("Rewa", "Sirmour", 24.5500, 81.6833),
    ("Rewa", "Mauganj", 24.6667, 81.8833),
    ("Dewas", "Dewas", 22.9676, 76.0534),
    ("Dewas", "Bagli", 23.1667, 76.3500),
    ("Dewas", "Khategaon", 22.5958, 76.9161),
    ("Ratlam", "Ratlam", 23.3315, 75.0367),
    ("Ratlam", "Alot", 23.7600, 75.5500),
    ("Ratlam", "Sailana", 23.4667, 74.9167),
    ("Mandsaur", "Mandsaur", 24.0734, 75.0696),
    ("Mandsaur", "Sitamau", 24.0167, 75.3500),
    ("Mandsaur", "Malhargarh", 24.2833, 74.9833),
    ("Dhar", "Dhar", 22.5993, 75.2979),
    ("Dhar", "Manawar", 22.2333, 75.0833),
    ("Dhar", "Kukshi", 22.2072, 74.7577),
    ("Khandwa", "Khandwa", 21.8333, 76.3500),
    ("Khandwa", "Pandhana", 21.6975, 76.2239),
    ("Khandwa", "Harsud", 22.1000, 76.7333),
    ("Chhindwara", "Chhindwara", 22.0576, 78.9396),
    ("Chhindwara", "Parasia", 22.1967, 78.7603),
    ("Chhindwara", "Sausar", 21.6544, 78.7964),
    ("Betul", "Betul", 21.9077, 77.9036),
    ("Betul", "Multai", 21.7747, 78.2580),
    ("Betul", "Bhainsdehi", 21.6447, 77.6686),
    ("Hoshangabad", "Hoshangabad", 22.7441, 77.7338),
    ("Hoshangabad", "Itarsi", 22.6167, 77.7667),
    ("Hoshangabad", "Sohagpur", 22.7000, 78.1833),
    ("Raisen", "Raisen", 23.3325, 77.7988),
    ("Raisen", "Bareli", 23.5167, 79.7333),
    ("Raisen", "Udaipura", 23.0833, 77.9833),
]

geology_types = ["Basalt", "Granite", "Vindhyan"]
aquifer_zones = ["Weathered", "Fractured", "Massive"]
trend_labels = ["Stable", "Watch", "Critical"]

print("🔌 Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print(f"📊 Generating {len(locations)} wells across Madhya Pradesh...")

inserted = 0
for i, (district, block, lat, lon) in enumerate(locations, 1):
    # Add small random offset to create variation
    lat_offset = (random.random() - 0.5) * 0.1  # ±0.05 degrees
    lon_offset = (random.random() - 0.5) * 0.1
    
    well_lat = lat + lat_offset
    well_lon = lon + lon_offset
    
    # Pick random characteristics
    geology = random.choice(geology_types)
    aquifer = random.choice(aquifer_zones)
    trend = random.choice(trend_labels)
    
    # Create well ID
    well_id = f"{district.upper()[:3]}-W{i:03d}"
    
    try:
        cur.execute("""
            INSERT INTO wells (well_id, district, block, lat_raw, lon_raw, geom, 
                              aquifer_zone, trend_label, geology_type, aquifer_classification)
            VALUES (%s, %s, %s, %s, %s, ST_GeogFromText('POINT(' || %s || ' ' || %s || ')'), 
                    %s, %s, %s, %s)
            ON CONFLICT (well_id) DO NOTHING
        """, (well_id, district, block, str(well_lat), str(well_lon), 
              str(well_lon), str(well_lat), aquifer, trend, geology, aquifer))
        
        if cur.rowcount > 0:
            inserted += 1
            if inserted % 10 == 0:
                print(f"  ✅ {inserted} wells inserted...")
    except Exception as e:
        print(f"  ⚠️ Failed to insert {well_id}: {e}")

conn.commit()

# Show final count
cur.execute("SELECT COUNT(*) FROM wells")
total = cur.fetchone()[0]

print(f"\n✅ Successfully inserted {inserted} new wells!")
print(f"📊 Total wells in database: {total}")

# Show distribution by district
print("\n📋 Wells by district:")
cur.execute("""
    SELECT district, COUNT(*) as count, 
           COUNT(CASE WHEN trend_label = 'Critical' THEN 1 END) as critical,
           COUNT(CASE WHEN trend_label = 'Watch' THEN 1 END) as watch,
           COUNT(CASE WHEN trend_label = 'Stable' THEN 1 END) as stable
    FROM wells 
    GROUP BY district 
    ORDER BY count DESC
    LIMIT 15
""")

for row in cur.fetchall():
    print(f"  {row[0]:15} → Total: {row[1]:3} | Critical: {row[2]:2} | Watch: {row[3]:2} | Stable: {row[4]:2}")

cur.close()
conn.close()

print("\n🎉 Done! Refresh your frontend to see all wells!")
print("🌐 https://groundwater-madhya-pradesh.vercel.app/")
