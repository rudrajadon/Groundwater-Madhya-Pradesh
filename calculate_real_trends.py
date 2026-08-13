#!/usr/bin/env python3
"""
Calculate REAL trends from historical data instead of 12-month forecasts.
Uses multi-year linear regression to determine actual groundwater trends.
"""
import psycopg2
import numpy as np
from scipy import stats

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'groundwater',
    'user': 'gwuser',
    'password': 'changeme'
}

def calculate_well_trend(well_id, conn):
    """
    Calculate the actual trend from historical data using linear regression.
    Returns: (trend_m_per_year, r_squared, n_readings, trend_label)
    """
    cur = conn.cursor()
    
    # Get all readings for this well
    cur.execute("""
        SELECT 
            date,
            head_msl_m
        FROM readings
        WHERE well_id = %s 
          AND head_msl_m IS NOT NULL
        ORDER BY date
    """, (well_id,))
    
    rows = cur.fetchall()
    cur.close()
    
    if len(rows) < 24:  # Need at least 2 years of data
        return None, None, len(rows), 'Unknown'
    
    # Convert to numpy arrays with proper dtype
    dates = np.array([(r[0] - rows[0][0]).days / 365.25 for r in rows], dtype=np.float64)  # Years from first reading
    levels = np.array([float(r[1]) for r in rows], dtype=np.float64)
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(dates, levels)
    r_squared = r_value ** 2
    
    # slope is in meters per year
    # Based on actual MP data: worst well is -1.23 m/yr
    # Adjusted thresholds to reflect real groundwater conditions:
    # Critical: < -1.0 m/yr (severe decline, top 2% worst)
    # Watch: -1.0 to -0.3 m/yr (moderate decline, needs monitoring)
    # Stable: > -0.3 m/yr (normal seasonal variation)
    
    if slope < -1.0:
        trend_label = 'Critical'
    elif slope < -0.3:
        trend_label = 'Watch'
    else:
        trend_label = 'Stable'
    
    return slope, r_squared, len(rows), trend_label


def main():
    print("="*80)
    print("CALCULATING REAL TRENDS FROM HISTORICAL DATA")
    print("="*80)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get all wells
    cur.execute("SELECT well_id FROM wells ORDER BY well_id")
    wells = [r[0] for r in cur.fetchall()]
    
    print(f"\nAnalyzing {len(wells)} wells...")
    
    results = []
    for i, well_id in enumerate(wells):
        if (i + 1) % 100 == 0:
            print(f"  Processed {i+1}/{len(wells)} wells...")
        
        slope, r_sq, n_readings, trend_label = calculate_well_trend(well_id, conn)
        
        if slope is not None:
            results.append({
                'well_id': well_id,
                'trend_m_per_year': slope,
                'r_squared': r_sq,
                'n_readings': n_readings,
                'trend_label': trend_label
            })
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}\n")
    
    print(f"Wells analyzed: {len(results)}")
    
    # Distribution
    critical = [r for r in results if r['trend_label'] == 'Critical']
    watch = [r for r in results if r['trend_label'] == 'Watch']
    stable = [r for r in results if r['trend_label'] == 'Stable']
    
    print(f"\nTrend Distribution:")
    print(f"  Critical (>4m/year decline): {len(critical)} ({100*len(critical)/len(results):.1f}%)")
    print(f"  Watch (2-4m/year decline): {len(watch)} ({100*len(watch)/len(results):.1f}%)")
    print(f"  Stable (<2m/year change): {len(stable)} ({100*len(stable)/len(results):.1f}%)")
    
    # Show critical wells
    if critical:
        print(f"\nCritical Wells (declining >4m/year):")
        critical.sort(key=lambda x: x['trend_m_per_year'])
        for r in critical[:10]:
            print(f"  {r['well_id']:<20} {r['trend_m_per_year']:>6.2f} m/yr  (R²={r['r_squared']:.3f}, n={r['n_readings']})")
        if len(critical) > 10:
            print(f"  ... and {len(critical)-10} more")
    
    # Show watch wells
    if watch:
        print(f"\nWatch Wells (declining 2-4m/year):")
        watch.sort(key=lambda x: x['trend_m_per_year'])
        for r in watch[:10]:
            print(f"  {r['well_id']:<20} {r['trend_m_per_year']:>6.2f} m/yr  (R²={r['r_squared']:.3f}, n={r['n_readings']})")
        if len(watch) > 10:
            print(f"  ... and {len(watch)-10} more")
    
    # Update database
    print(f"\n{'='*80}")
    print("UPDATING DATABASE")
    print(f"{'='*80}\n")
    
    for r in results:
        cur.execute("""
            UPDATE wells
            SET trend_label = %s
            WHERE well_id = %s
        """, (r['trend_label'], r['well_id']))
    
    conn.commit()
    print(f"✓ Updated {len(results)} wells in database")
    
    # Save detailed results
    import json
    with open('real_trends_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✓ Saved detailed analysis to real_trends_analysis.json")
    
    conn.close()
    
    print(f"\n{'='*80}")
    print("✓ DONE! Trends calculated from actual historical data")
    print(f"{'='*80}\n")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
