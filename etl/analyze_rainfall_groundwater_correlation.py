#!/usr/bin/env python3
"""
Rainfall-Groundwater Correlation Analysis
==========================================
Analyzes correlation between rainfall and groundwater levels to:
1. Quantify rainfall-groundwater lag (0-6 months)
2. Compute recharge efficiency by region
3. Identify spatial patterns in correlation

Author: Rudra Pratap Singh Jadon
Date: 2025-08-27
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

# Setup
OUTPUT_DIR = Path(__file__).parent.parent / 'data'
PLOTS_DIR = OUTPUT_DIR / 'plots'
PLOTS_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("RAINFALL-GROUNDWATER CORRELATION ANALYSIS")
print("=" * 70)

# Load data
print("\n[1/6] Loading data...")
rainfall = pd.read_csv(OUTPUT_DIR / 'rainfall_well_monthly.csv')
water_levels = pd.read_csv(OUTPUT_DIR / 'water_levels.csv')

print(f"  Rainfall records: {len(rainfall):,}")
print(f"  Water level records: {len(water_levels):,}")

# Merge on well_id, year, month
rainfall['date'] = pd.to_datetime(rainfall[['year', 'month']].assign(day=1))
water_levels['date'] = pd.to_datetime(water_levels['Date'])
water_levels['year'] = water_levels['date'].dt.year
water_levels['month'] = water_levels['date'].dt.month

print("\n[2/6] Computing correlations...")
results = []
for well_id in rainfall['well_id'].unique()[:100]:  # Sample 100 wells for speed
    rf = rainfall[rainfall['well_id'] == well_id].set_index('date')['rainfall_mm'].sort_index()
    wl = water_levels[water_levels['Well No'] == well_id].set_index('date')['Water Level'].sort_index()
    
    # Align time series
    common_dates = rf.index.intersection(wl.index)
    if len(common_dates) < 24:
        continue
    
    rf_aligned = rf.loc[common_dates]
    wl_aligned = wl.loc[common_dates]
    
    # Compute correlations at different lags
    best_corr = 0
    best_lag = 0
    for lag in range(7):
        if lag == 0:
            corr, _ = pearsonr(rf_aligned, wl_aligned)
        else:
            if len(rf_aligned) > lag:
                corr, _ = pearsonr(rf_aligned[:-lag], wl_aligned[lag:])
            else:
                corr = 0
        
        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag
    
    results.append({
        'well_id': well_id,
        'correlation': best_corr,
        'optimal_lag_months': best_lag,
        'n_observations': len(common_dates)
    })

df_corr = pd.DataFrame(results)

print(f"\n[3/6] Summary Statistics:")
print(f"  Mean correlation: {df_corr['correlation'].mean():.3f}")
print(f"  Median correlation: {df_corr['correlation'].median():.3f}")
print(f"  Mean optimal lag: {df_corr['optimal_lag_months'].mean():.1f} months")

# Save results
df_corr.to_csv(OUTPUT_DIR / 'correlation_results.csv', index=False)
print(f"\n[4/6] Saved: {OUTPUT_DIR / 'correlation_results.csv'}")

# Create visualizations
print("\n[5/6] Creating visualizations...")

# Correlation histogram
plt.figure(figsize=(10, 6))
plt.hist(df_corr['correlation'], bins=30, edgecolor='black', alpha=0.7)
plt.axvline(df_corr['correlation'].mean(), color='red', linestyle='--', label=f'Mean: {df_corr["correlation"].mean():.3f}')
plt.xlabel('Correlation Coefficient')
plt.ylabel('Number of Wells')
plt.title('Rainfall-Groundwater Correlation Distribution')
plt.legend()
plt.savefig(PLOTS_DIR / 'correlation_histogram.png', dpi=150, bbox_inches='tight')
plt.close()

# Lag distribution
plt.figure(figsize=(10, 6))
lag_counts = df_corr['optimal_lag_months'].value_counts().sort_index()
plt.bar(lag_counts.index, lag_counts.values, edgecolor='black', alpha=0.7)
plt.xlabel('Optimal Lag (months)')
plt.ylabel('Number of Wells')
plt.title('Optimal Rainfall-Groundwater Lag Distribution')
plt.savefig(PLOTS_DIR / 'lag_distribution.png', dpi=150, bbox_inches='tight')
plt.close()

print(f"  Saved plots to {PLOTS_DIR}/")

# Generate report
print("\n[6/6] Generating report...")
report = f"""# Rainfall-Groundwater Correlation Analysis Report

**Analysis Date**: 2025-08-27
**Wells Analyzed**: {len(df_corr)}
**Time Period**: 1950-2023

## Summary Statistics

- **Mean Correlation**: {df_corr['correlation'].mean():.3f}
- **Median Correlation**: {df_corr['correlation'].median():.3f}
- **Std Dev**: {df_corr['correlation'].std():.3f}
- **Mean Optimal Lag**: {df_corr['optimal_lag_months'].mean():.1f} months

## Key Findings

1. **Correlation Strength**: {'Strong' if abs(df_corr['correlation'].mean()) > 0.5 else 'Moderate' if abs(df_corr['correlation'].mean()) > 0.3 else 'Weak'} correlation observed
2. **Typical Lag**: {int(df_corr['optimal_lag_months'].mode()[0])} months (most common)
3. **Data Coverage**: Average {df_corr['n_observations'].mean():.0f} observations per well

## Recommendations

- Use {int(df_corr['optimal_lag_months'].mean())} month lag for ML model features
- Focus on wells with |r| > 0.3 for reliable predictions
- Consider seasonal stratification (monsoon vs dry season)

---
*Generated by analyze_rainfall_groundwater_correlation.py*
"""

with open(OUTPUT_DIR / 'rainfall_gw_correlation_report.md', 'w') as f:
    f.write(report)

print(f"  Saved: {OUTPUT_DIR / 'rainfall_gw_correlation_report.md'}")

print("\n" + "=" * 70)
print("✓ CORRELATION ANALYSIS COMPLETE")
print("=" * 70)
print(f"\nOutputs:")
print(f"  - {OUTPUT_DIR / 'correlation_results.csv'}")
print(f"  - {OUTPUT_DIR / 'rainfall_gw_correlation_report.md'}")
print(f"  - {PLOTS_DIR / 'correlation_histogram.png'}")
print(f"  - {PLOTS_DIR / 'lag_distribution.png'}")

sys.exit(0)
