#!/usr/bin/env python3
"""
One-shot data quality fix:
  1. Bad dates in water_levels.csv  (2074/2075 → 1974/1975, 2031 → 1931)
  2. Elevation outlier in wells.csv  (TKM079A-OW 3313 → 331)
  3. Fill missing elevations with district median
Writes fixed files in-place (originals backed up as *.bak.csv).
"""
import pandas as pd
import numpy as np
import shutil, sys

# ── helpers ───────────────────────────────────────────────────────────────────
def backup(path):
    bak = path.replace('.csv', '.bak.csv')
    shutil.copy2(path, bak)
    print(f"  backed up → {bak}")

# ════════════════════════════════════════════════════════════════════════════════
# 1. WATER LEVELS
# ════════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("Fixing data/water_levels.csv")
print("=" * 60)

wl = pd.read_csv('data/water_levels.csv')
backup('data/water_levels.csv')

wl['date'] = pd.to_datetime(wl['date'], format='mixed')

before = len(wl)

# OCR errors: 2074 → 1974, 2075 → 1975, 2031 → 1931
def fix_year(dt):
    y = dt.year
    if y == 2074: return dt.replace(year=1974)
    if y == 2075: return dt.replace(year=1975)
    if y == 2031: return dt.replace(year=1931)
    return dt

wl['date'] = wl['date'].apply(fix_year)

# 2026 rows are real recent measurements — keep them, just cap at today
# (Some MDB export quirk puts Jan-2026 readings; they're valid, not OCR errors)
still_future = wl[wl['date'].dt.year > 2025]
print(f"  Rows still future after OCR fix: {len(still_future)}")
# Keep 2026 data — it is genuinely recent measurements up to Jan 2026
# Only drop anything beyond 2026 (none remain after the fix above)
wl = wl[wl['date'].dt.year <= 2026]

# Drop physically impossible water levels
wl = wl[(wl['Water Level'] >= 0) & (wl['Water Level'] <= 100)]

print(f"  Rows before: {before:,}  →  after: {len(wl):,}  (removed {before-len(wl)})")
print(f"  Date range: {wl['date'].min().date()} → {wl['date'].max().date()}")
print(f"  Water level range: {wl['Water Level'].min():.2f} – {wl['Water Level'].max():.2f} m")

wl.to_csv('data/water_levels.csv', index=False)
print("  ✓ Saved data/water_levels.csv")

# ════════════════════════════════════════════════════════════════════════════════
# 2. WELLS
# ════════════════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("Fixing data/wells.csv")
print("=" * 60)

wells = pd.read_csv('data/wells.csv')
backup('data/wells.csv')

col = 'Elevation of Ground Level'

# Fix decimal-shift outlier (3313 → 331.3)
mask_outlier = wells[col] > 1500
n_out = mask_outlier.sum()
print(f"  Elevation outliers (>1500 m): {n_out}")
if n_out:
    print("  Fixing by dividing by 10:")
    print(wells.loc[mask_outlier, ['Well No', col]].to_string())
    wells.loc[mask_outlier, col] = wells.loc[mask_outlier, col] / 10.0

# Fill missing elevations with district median, then overall median
district_med = (
    wells.dropna(subset=[col])
    .groupby('District')[col].median()
)
overall_med = wells[col].median()

missing_before = wells[col].isna().sum()

def fill_elev(row):
    if pd.notna(row[col]):
        return row[col]
    d_med = district_med.get(row['District'])
    return d_med if pd.notna(d_med) else overall_med

wells[col] = wells.apply(fill_elev, axis=1)
missing_after = wells[col].isna().sum()

print(f"  Missing elevation: {missing_before} → {missing_after}")
print(f"  Elevation range after fix: {wells[col].min():.1f} – {wells[col].max():.1f} m")

wells.to_csv('data/wells.csv', index=False)
print("  ✓ Saved data/wells.csv")

# ════════════════════════════════════════════════════════════════════════════════
# 3. SUMMARY
# ════════════════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
print("✓ All data quality fixes applied")
print("=" * 60)
print(f"  water_levels.csv : {len(wl):,} rows, "
      f"{wl['Well No'].nunique()} wells, "
      f"{wl['date'].min().year}–{wl['date'].max().year}")
print(f"  wells.csv        : {len(wells):,} rows, "
      f"elevation {wells[col].min():.0f}–{wells[col].max():.0f} m")
