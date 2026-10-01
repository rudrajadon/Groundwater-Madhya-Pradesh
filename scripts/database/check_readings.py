#!/usr/bin/env python3
import psycopg2

DATABASE_URL = "postgresql://groundwater_user:XCmOvmSsepDzDnCRRY9K08ALjA96JGwZ@dpg-dat0ojjncjis73cllkng-a.oregon-postgres.render.com/groundwater_l5m7"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Check some wells with data
cur.execute("""
    SELECT well_id, COUNT(*) as readings 
    FROM readings 
    GROUP BY well_id 
    ORDER BY readings DESC 
    LIMIT 5
""")
print("Top 5 wells with most readings:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} readings")

# Check if TKM008-OW has data
cur.execute("SELECT COUNT(*) FROM readings WHERE well_id = 'TKM008-OW'")
print(f"\nTKM008-OW has {cur.fetchone()[0]} readings")

cur.close()
conn.close()
