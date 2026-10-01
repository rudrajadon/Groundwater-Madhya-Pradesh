#!/usr/bin/env python3
"""
PROPERLY calculate trend labels based on actual water level decline rates
"""

import psycopg2

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

print("🔌 Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("\n📊 Checking data availability...")
cur.execute("SELECT COUNT(DISTINCT well_id) FROM readings WHERE head_msl_m IS NOT NULL")
wells_with_data = cur.fetchone()[0]
print(f"   Wells with head_msl_m data: {wells_with_data}")

if wells_with_data == 0:
    print("\n❌ NO DATA! Readings weren't loaded properly!")
    print("   The water_levels.csv file wasn't imported.")
    cur.close()
    conn.close()
    exit(1)

print(f"\n📈 Calculating REAL trends for {wells_with_data} wells...")

# Calculate trend using simpler approach: compare recent vs old average
cur.execute("""
    WITH well_readings AS (
        SELECT 
            well_id,
            date,
            head_msl_m,
            ROW_NUMBER() OVER (PARTITION BY well_id ORDER BY date DESC) as recency_rank,
            COUNT(*) OVER (PARTITION BY well_id) as total_readings
        FROM readings
        WHERE head_msl_m IS NOT NULL
    ),
    well_trends AS (
        SELECT 
            well_id,
            total_readings,
            -- Average of most recent 25% of readings
            AVG(CASE WHEN recency_rank <= GREATEST(6, total_readings * 0.25) THEN head_msl_m END) as recent_avg,
            -- Average of oldest 25% of readings
            AVG(CASE WHEN recency_rank > total_readings * 0.75 THEN head_msl_m END) as old_avg,
            -- Calculate change
            AVG(CASE WHEN recency_rank <= GREATEST(6, total_readings * 0.25) THEN head_msl_m END) - 
            AVG(CASE WHEN recency_rank > total_readings * 0.75 THEN head_msl_m END) as total_change,
            -- Time span in years (approximate)
            EXTRACT(YEAR FROM MAX(date)) - EXTRACT(YEAR FROM MIN(date)) + 1 as years_span
        FROM well_readings
        GROUP BY well_id, total_readings
        HAVING COUNT(*) >= 12
    ),
    well_classifications AS (
        SELECT 
            well_id,
            total_readings,
            recent_avg,
            old_avg,
            total_change,
            years_span,
            -- Annual decline rate (negative = declining)
            CASE 
                WHEN years_span > 0 THEN total_change / years_span
                ELSE 0
            END as annual_change,
            -- Classify based on total change and rate
            CASE
                WHEN total_change < -5 OR (years_span > 0 AND total_change / years_span < -1.0) THEN 'Critical'
                WHEN total_change < -2 OR (years_span > 0 AND total_change / years_span < -0.3) THEN 'Watch'
                ELSE 'Stable'
            END as calculated_trend
        FROM well_trends
    )
    UPDATE wells w
    SET trend_label = c.calculated_trend
    FROM well_classifications c
    WHERE w.well_id = c.well_id
    RETURNING w.well_id, w.trend_label
""")

results = cur.fetchall()
conn.commit()

print(f"\n✅ Updated {len(results)} wells with calculated trends")

# Show distribution
cur.execute("""
    SELECT trend_label, COUNT(*) as count
    FROM wells
    WHERE trend_label IS NOT NULL
    GROUP BY trend_label
    ORDER BY 
        CASE trend_label
            WHEN 'Critical' THEN 1
            WHEN 'Watch' THEN 2
            WHEN 'Stable' THEN 3
        END
""")

print("\n📊 REAL Trend Distribution:")
for row in cur.fetchall():
    label, count = row
    print(f"   {label:10} → {count:5} wells")

# Show some examples
print("\n🔍 Sample wells with trends:")
cur.execute("""
    WITH well_changes AS (
        SELECT 
            r.well_id,
            w.trend_label,
            COUNT(*) as readings,
            MAX(r.head_msl_m) - MIN(r.head_msl_m) as total_change,
            (EXTRACT(YEAR FROM MAX(r.date)) - EXTRACT(YEAR FROM MIN(r.date)) + 1) as years
        FROM readings r
        JOIN wells w ON r.well_id = w.well_id
        WHERE r.head_msl_m IS NOT NULL AND w.trend_label IS NOT NULL
        GROUP BY r.well_id, w.trend_label
        HAVING COUNT(*) >= 12
    )
    SELECT 
        well_id, 
        trend_label, 
        readings, 
        ROUND(total_change::numeric, 2) as change_m,
        years,
        ROUND((total_change / NULLIF(years, 0))::numeric, 2) as rate_m_per_year
    FROM well_changes
    ORDER BY 
        CASE trend_label
            WHEN 'Critical' THEN 1
            WHEN 'Watch' THEN 2  
            WHEN 'Stable' THEN 3
        END,
        rate_m_per_year
    LIMIT 10
""")

for row in cur.fetchall():
    well_id, trend, readings, change, years, rate = row
    print(f"   {well_id:15} {trend:10} ({readings:3} readings) → {change:+7.2f}m over {years}y ({rate:+.2f} m/y)")

cur.close()
conn.close()

print("\n🎉 Done! Wells now have REAL trend labels based on actual decline rates!")
print("🌐 Refresh: https://groundwater-madhya-pradesh.vercel.app/")
