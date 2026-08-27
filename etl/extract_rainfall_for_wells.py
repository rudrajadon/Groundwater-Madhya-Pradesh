#!/usr/bin/env python3
"""
Extract IMD Rainfall Data for MP Groundwater Wells
===================================================
Reads IMD 0.25° gridded rainfall NetCDF files (1950-2024) and extracts
monthly rainfall time-series for each monitoring well location in Madhya Pradesh.

Input:
  - NetCDF files: /Users/rudrajadon/Downloads/Rainfall_IMD_NC/RF25_ind{year}_rfp25.nc
  - Well locations: From PostgreSQL database (wells table)

Output:
  - CSV: data/rainfall_well_monthly.csv
    Columns: well_id, year, month, rainfall_mm, lat, lon
  - Summary stats and visualization

Method:
  - Nearest-neighbor interpolation (0.25° grid → well location)
  - Monthly aggregation: sum of daily rainfall
  - Handles missing data and leap years

Author: Rudra Pratap Singh Jadon
Date: 2025-08-27
"""

import os
import sys
import glob
import warnings
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import netCDF4 as nc
from scipy.spatial import cKDTree

warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

RAINFALL_DIR = Path('/Users/rudrajadon/Downloads/Rainfall_IMD_NC')
OUTPUT_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_FILE = OUTPUT_DIR / 'rainfall_well_monthly.csv'
DB_WELLS_CSV = OUTPUT_DIR / 'wells.csv'  # Fallback if DB not available

# Madhya Pradesh bounds
MP_LAT_MIN, MP_LAT_MAX = 21.0, 26.5
MP_LON_MIN, MP_LON_MAX = 74.0, 82.5

# Year range
START_YEAR = 1950
END_YEAR = 2024

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def load_wells_from_db() -> pd.DataFrame:
    """Load well locations from PostgreSQL database."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname='groundwater',
            user='gwuser',
            password='changeme',
            host='localhost',
            port=5432
        )
        query = """
            SELECT well_id, latitude, longitude, district, geology_type
            FROM wells
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            AND latitude BETWEEN 21.0 AND 26.5
            AND longitude BETWEEN 74.0 AND 82.5
            ORDER BY well_id
        """
        wells = pd.read_sql(query, conn)
        conn.close()
        print(f"  ✓ Loaded {len(wells)} wells from PostgreSQL")
        return wells
    except Exception as e:
        print(f"  ⚠ PostgreSQL connection failed: {e}")
        return None


def load_wells_from_csv() -> pd.DataFrame:
    """Fallback: Load well locations from CSV file."""
    if not DB_WELLS_CSV.exists():
        print(f"  ✗ ERROR: {DB_WELLS_CSV} not found")
        sys.exit(1)
    
    wells = pd.read_csv(DB_WELLS_CSV)
    
    # Check column names and convert Northing/Easting to Lat/Lon if needed
    if 'Northing' in wells.columns and 'Easting' in wells.columns:
        wells = wells.rename(columns={
            'Northing': 'latitude',
            'Easting': 'longitude'
        })
    elif 'Latitude' in wells.columns and 'Longitude' in wells.columns:
        wells = wells.rename(columns={
            'Latitude': 'latitude',
            'Longitude': 'longitude'
        })
    
    # Filter to MP region
    wells = wells[
        (wells['latitude'].between(MP_LAT_MIN, MP_LAT_MAX)) &
        (wells['longitude'].between(MP_LON_MIN, MP_LON_MAX))
    ].copy()
    
    wells = wells.rename(columns={
        'Well No': 'well_id',
        'District': 'district'
    })
    
    # Add geology_type if not present
    if 'geology_type' not in wells.columns:
        wells['geology_type'] = wells.get('geology_type', 'Unknown')
    
    print(f"  ✓ Loaded {len(wells)} wells from CSV")
    return wells[['well_id', 'latitude', 'longitude', 'district', 'geology_type']]


def build_spatial_tree(nc_lat: np.ndarray, nc_lon: np.ndarray) -> Tuple[cKDTree, np.ndarray]:
    """Build KD-tree for fast nearest-neighbor lookup."""
    # Create grid of all lat/lon points
    lon_grid, lat_grid = np.meshgrid(nc_lon, nc_lat)
    points = np.column_stack([lat_grid.ravel(), lon_grid.ravel()])
    tree = cKDTree(points)
    return tree, points


def extract_rainfall_for_year(year: int, wells: pd.DataFrame, tree: cKDTree, 
                               lat_idx_map: Dict, lon_idx_map: Dict) -> pd.DataFrame:
    """Extract monthly rainfall for all wells for a given year."""
    nc_file = RAINFALL_DIR / f'RF25_ind{year}_rfp25.nc'
    
    if not nc_file.exists():
        print(f"    ⚠ Missing: {nc_file.name}")
        return pd.DataFrame()
    
    try:
        ds = nc.Dataset(nc_file, 'r')
        
        # Handle both uppercase and lowercase variable names
        var_names = list(ds.variables.keys())
        lat_var = 'LATITUDE' if 'LATITUDE' in var_names else 'lat'
        lon_var = 'LONGITUDE' if 'LONGITUDE' in var_names else 'lon'
        time_var = 'TIME' if 'TIME' in var_names else 'time'
        rain_var = 'RAINFALL' if 'RAINFALL' in var_names else 'rf'
        
        lat = ds.variables[lat_var][:]
        lon = ds.variables[lon_var][:]
        time = ds.variables[time_var][:]
        rainfall = ds.variables[rain_var][:]  # shape: (days, lat, lon)
        
        # Convert TIME to dates
        base_date = datetime(1900, 12, 31)
        dates = [base_date + timedelta(days=int(t)) for t in time]
        
        # Group by month
        df_dates = pd.DataFrame({'date': dates, 'day_idx': np.arange(len(dates))})
        df_dates['year'] = df_dates['date'].dt.year
        df_dates['month'] = df_dates['date'].dt.month
        
        records = []
        
        for _, well in wells.iterrows():
            # Find nearest grid cell
            dist, idx = tree.query([well['latitude'], well['longitude']])
            lat_val, lon_val = tree.data[idx]
            
            # Get indices in the rainfall array
            lat_i = np.argmin(np.abs(lat - lat_val))
            lon_i = np.argmin(np.abs(lon - lon_val))
            
            # Extract daily rainfall for this grid cell
            well_rainfall = rainfall[:, lat_i, lon_i]
            
            # Aggregate by month
            df_dates['rainfall'] = well_rainfall
            monthly = df_dates.groupby(['year', 'month'])['rainfall'].sum().reset_index()
            
            for _, row in monthly.iterrows():
                records.append({
                    'well_id': well['well_id'],
                    'year': int(row['year']),
                    'month': int(row['month']),
                    'rainfall_mm': float(row['rainfall']),
                    'lat': well['latitude'],
                    'lon': well['longitude'],
                    'district': well['district'],
                    'geology_type': well['geology_type']
                })
        
        ds.close()
        return pd.DataFrame(records)
    
    except Exception as e:
        print(f"    ✗ ERROR processing {nc_file.name}: {e}")
        return pd.DataFrame()


def compute_summary_stats(df: pd.DataFrame) -> None:
    """Compute and display summary statistics."""
    print("\n" + "=" * 70)
    print("RAINFALL DATA SUMMARY")
    print("=" * 70)
    
    print(f"\n1. Coverage:")
    print(f"   Total records: {len(df):,}")
    print(f"   Unique wells: {df['well_id'].nunique()}")
    print(f"   Year range: {df['year'].min()} - {df['year'].max()}")
    print(f"   Months covered: {len(df) / df['well_id'].nunique():.1f} per well")
    
    print(f"\n2. Rainfall Statistics (mm/month):")
    print(f"   Mean: {df['rainfall_mm'].mean():.2f}")
    print(f"   Median: {df['rainfall_mm'].median():.2f}")
    print(f"   Std Dev: {df['rainfall_mm'].std():.2f}")
    print(f"   Min: {df['rainfall_mm'].min():.2f}")
    print(f"   Max: {df['rainfall_mm'].max():.2f}")
    
    print(f"\n3. Missing Data:")
    missing_pct = (df['rainfall_mm'] == 0).sum() / len(df) * 100
    print(f"   Zero rainfall months: {(df['rainfall_mm'] == 0).sum():,} ({missing_pct:.2f}%)")
    print(f"   Non-zero months: {(df['rainfall_mm'] > 0).sum():,}")
    
    print(f"\n4. Seasonal Patterns (Mean rainfall by month):")
    monthly_avg = df.groupby('month')['rainfall_mm'].mean().sort_index()
    for month, avg in monthly_avg.items():
        month_name = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month]
        bar = '█' * int(avg / 20)  # Scale for display
        print(f"   {month_name:>3}: {avg:6.1f} mm  {bar}")
    
    print(f"\n5. District Coverage:")
    district_counts = df.groupby('district')['well_id'].nunique().sort_values(ascending=False)
    for dist, count in district_counts.head(10).items():
        print(f"   {dist}: {count} wells")
    
    print(f"\n6. Data Quality Checks:")
    # Check for anomalies
    high_rainfall = df[df['rainfall_mm'] > 1000]
    if len(high_rainfall) > 0:
        print(f"   ⚠ {len(high_rainfall)} months with >1000mm rainfall (check for errors)")
    else:
        print(f"   ✓ No extreme outliers detected")
    
    # Check temporal consistency
    wells_with_gaps = []
    for well_id in df['well_id'].unique():
        well_data = df[df['well_id'] == well_id].sort_values(['year', 'month'])
        expected_months = (well_data['year'].max() - well_data['year'].min() + 1) * 12
        actual_months = len(well_data)
        if actual_months < expected_months * 0.9:  # More than 10% missing
            wells_with_gaps.append(well_id)
    
    if len(wells_with_gaps) > 0:
        print(f"   ⚠ {len(wells_with_gaps)} wells with >10% missing months")
    else:
        print(f"   ✓ All wells have good temporal coverage")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXTRACTION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("IMD RAINFALL EXTRACTION FOR MP GROUNDWATER WELLS")
    print("=" * 70)
    print(f"Rainfall data directory: {RAINFALL_DIR}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Year range: {START_YEAR}-{END_YEAR}")
    
    # ─── Step 1: Load well locations ──────────────────────────────────────
    print("\n[1/5] Loading well locations...")
    wells = load_wells_from_db()
    if wells is None or len(wells) == 0:
        wells = load_wells_from_csv()
    
    print(f"      Wells in MP region: {len(wells)}")
    print(f"      Lat range: {wells['latitude'].min():.3f}° - {wells['latitude'].max():.3f}°")
    print(f"      Lon range: {wells['longitude'].min():.3f}° - {wells['longitude'].max():.3f}°")
    
    # ─── Step 2: Build spatial index ──────────────────────────────────────
    print("\n[2/5] Building spatial index...")
    # Load a sample NetCDF to get grid structure
    sample_nc = RAINFALL_DIR / f'RF25_ind{END_YEAR}_rfp25.nc'
    ds = nc.Dataset(sample_nc, 'r')
    
    # Handle both uppercase and lowercase variable names
    var_names = list(ds.variables.keys())
    lat_var = 'LATITUDE' if 'LATITUDE' in var_names else 'lat'
    lon_var = 'LONGITUDE' if 'LONGITUDE' in var_names else 'lon'
    
    nc_lat = ds.variables[lat_var][:]
    nc_lon = ds.variables[lon_var][:]
    ds.close()
    
    tree, points = build_spatial_tree(nc_lat, nc_lon)
    print(f"      ✓ Spatial KD-tree built ({len(points):,} grid cells)")
    
    # Create index maps
    lat_idx_map = {lat: i for i, lat in enumerate(nc_lat)}
    lon_idx_map = {lon: i for i, lon in enumerate(nc_lon)}
    
    # ─── Step 3: Extract rainfall year by year ────────────────────────────
    print("\n[3/5] Extracting rainfall data...")
    print(f"      Processing {END_YEAR - START_YEAR + 1} years × {len(wells)} wells")
    
    all_data = []
    years_processed = 0
    
    for year in range(START_YEAR, END_YEAR + 1):
        if year % 10 == 0:
            print(f"      {year}...", end=' ', flush=True)
        
        year_data = extract_rainfall_for_year(year, wells, tree, lat_idx_map, lon_idx_map)
        if len(year_data) > 0:
            all_data.append(year_data)
            years_processed += 1
    
    print(f"\n      ✓ Processed {years_processed} years")
    
    # ─── Step 4: Combine and save ─────────────────────────────────────────
    print("\n[4/5] Combining and saving results...")
    if len(all_data) == 0:
        print("      ✗ ERROR: No data extracted")
        sys.exit(1)
    
    df_rainfall = pd.concat(all_data, ignore_index=True)
    df_rainfall = df_rainfall.sort_values(['well_id', 'year', 'month']).reset_index(drop=True)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df_rainfall.to_csv(OUTPUT_FILE, index=False)
    print(f"      ✓ Saved {len(df_rainfall):,} records to {OUTPUT_FILE}")
    print(f"      File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB")
    
    # ─── Step 5: Summary statistics ───────────────────────────────────────
    print("\n[5/5] Computing summary statistics...")
    compute_summary_stats(df_rainfall)
    
    print("\n" + "=" * 70)
    print("✓ RAINFALL EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"  1. Review summary stats above")
    print(f"  2. Run correlation analysis: python etl/analyze_rainfall_groundwater_correlation.py")
    print(f"  3. Load to database: python etl/load_rainfall_to_postgres.py")
    print(f"  4. Update ML model to include rainfall features")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
