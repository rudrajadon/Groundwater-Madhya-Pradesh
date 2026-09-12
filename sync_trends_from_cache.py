#!/usr/bin/env python3
"""
Sync trend_label in wells table with the cached forecast trend labels.
The forecast_cache has the CORRECT trends, but wells.trend_label is outdated.
"""
import psycopg2
import os

DATABASE_URL = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

def main():
    print("=" * 70)
    print("SYNCING TREND LABELS FROM FORECAST CACHE")
    print("=" * 70)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Count wells with mismatched trends
    cur.execute("""
        SELECT COUNT(*)
        FROM wells
        WHERE forecast_cache IS NOT NULL
        AND trend_label != forecast_cache->>'trend_label'
    """)
    mismatched = cur.fetchone()[0]
    print(f"\n⚠️  Found {mismatched} wells with mismatched trend labels")
    
    # Show some examples
    cur.execute("""
        SELECT well_id, trend_label, forecast_cache->>'trend_label' as cache_trend
        FROM wells
        WHERE forecast_cache IS NOT NULL
        AND trend_label != forecast_cache->>'trend_label'
        LIMIT 10
    """)
    
    print(f"\n📋 Sample mismatches:")
    for row in cur.fetchall():
        print(f"   {row[0]}: DB={row[1]} → Cache={row[2]}")
    
    # Update all trends from cache
    print(f"\n🔄 Updating {mismatched} wells...")
    cur.execute("""
        UPDATE wells
        SET 
            trend_label = forecast_cache->>'trend_label',
            forecast_decline_m = (forecast_cache->>'decline_m')::numeric
        WHERE forecast_cache IS NOT NULL
        AND trend_label != forecast_cache->>'trend_label'
    """)
    
    updated = cur.rowcount
    conn.commit()
    
    print(f"✅ Updated {updated} wells!")
    
    # Verify
    cur.execute("""
        SELECT 
            trend_label,
            COUNT(*) as count
        FROM wells
        WHERE trend_label IS NOT NULL
        GROUP BY trend_label
        ORDER BY count DESC
    """)
    
    print(f"\n{'='*70}")
    print(f"✅ TREND DISTRIBUTION (AFTER SYNC):")
    print(f"{'='*70}")
    for row in cur.fetchall():
        print(f"  {row[0]:12} {row[1]:4} wells")
    print(f"{'='*70}")
    
    # Verify no more mismatches
    cur.execute("""
        SELECT COUNT(*)
        FROM wells
        WHERE forecast_cache IS NOT NULL
        AND trend_label != forecast_cache->>'trend_label'
    """)
    remaining = cur.fetchone()[0]
    
    if remaining == 0:
        print(f"\n🎉 Perfect! All trends are now in sync!")
    else:
        print(f"\n⚠️  Warning: {remaining} wells still have mismatches")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
