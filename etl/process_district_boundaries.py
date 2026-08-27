#!/usr/bin/env python3
"""
Process MP district boundaries shapefile and convert to GeoJSON for web use.
Also validates geometry and creates simplified versions for performance.
"""
import geopandas as gpd
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
SHP_PATH = BASE_DIR / "23" / "MP_DISTRICT_BDY.shp"
OUTPUT_DIR = BASE_DIR / "frontend" / "public" / "geo"
OUTPUT_FILE = OUTPUT_DIR / "mp_districts.geojson"
OUTPUT_SIMPLIFIED = OUTPUT_DIR / "mp_districts_simplified.geojson"

def main():
    print("=" * 70)
    print("Processing Madhya Pradesh District Boundaries")
    print("=" * 70)
    
    # 1. Load shapefile
    print(f"\n[1/6] Loading shapefile: {SHP_PATH}")
    gdf = gpd.read_file(SHP_PATH)
    print(f"  ✓ Loaded {len(gdf)} districts")
    print(f"  ✓ CRS: {gdf.crs}")
    print(f"  ✓ Columns: {list(gdf.columns)}")
    
    # 2. Show sample data
    print(f"\n[2/6] Sample data:")
    print(gdf.head(3))
    
    # 3. Validate and clean geometry
    print(f"\n[3/6] Validating geometry...")
    invalid = gdf[~gdf.is_valid]
    if len(invalid) > 0:
        print(f"  ⚠ Found {len(invalid)} invalid geometries, fixing...")
        gdf['geometry'] = gdf.geometry.buffer(0)
    else:
        print(f"  ✓ All geometries valid")
    
    # 4. Transform to WGS84 (EPSG:4326) for web use
    print(f"\n[4/6] Transforming to WGS84 (EPSG:4326)...")
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
        print(f"  ✓ Transformed from {SHP_PATH} to WGS84")
    else:
        print(f"  ✓ Already in WGS84")
    
    # 5. Clean up columns and add metadata
    print(f"\n[5/6] Preparing export data...")
    
    # Standardize column names
    column_map = {}
    for col in gdf.columns:
        if col != 'geometry':
            col_upper = str(col).upper()
            if col_upper == 'DISTRICT' or ('DIST' in col_upper and 'LGD' not in col_upper):
                column_map[col] = 'district'
            elif col_upper == 'STATE' or col_upper == 'STATE_UT':
                column_map[col] = 'state'
    
    if column_map:
        gdf = gdf.rename(columns=column_map)
        print(f"  ✓ Renamed columns: {column_map}")
    
    # Keep only essential columns
    keep_cols = ['geometry']
    if 'district' in gdf.columns:
        keep_cols.append('district')
        # Clean district names
        gdf.loc[:, 'district'] = gdf['district'].astype(str).str.strip()
        print(f"  ✓ Districts ({len(gdf['district'].unique())} unique):")
        print(f"    {sorted(gdf['district'].unique())}")
    if 'state' in gdf.columns:
        keep_cols.append('state')
    
    gdf_export = gdf[keep_cols].copy()
    
    # 6. Export as GeoJSON
    print(f"\n[6/6] Exporting GeoJSON...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Full resolution
    gdf_export.to_file(OUTPUT_FILE, driver='GeoJSON')
    file_size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
    print(f"  ✓ Exported full resolution: {OUTPUT_FILE}")
    print(f"    Size: {file_size_mb:.2f} MB")
    
    # Simplified version (for faster web rendering)
    print(f"\n  Creating simplified version (tolerance=0.001°)...")
    gdf_simplified = gdf_export.copy()
    gdf_simplified['geometry'] = gdf_simplified.geometry.simplify(tolerance=0.001, preserve_topology=True)
    gdf_simplified.to_file(OUTPUT_SIMPLIFIED, driver='GeoJSON')
    simplified_size_mb = OUTPUT_SIMPLIFIED.stat().st_size / 1024 / 1024
    print(f"  ✓ Exported simplified: {OUTPUT_SIMPLIFIED}")
    print(f"    Size: {simplified_size_mb:.2f} MB (reduced by {100*(1-simplified_size_mb/file_size_mb):.1f}%)")
    
    # Summary statistics
    print(f"\n" + "=" * 70)
    print(f"✅ SUCCESS!")
    print(f"=" * 70)
    print(f"  Total districts: {len(gdf_export)}")
    if 'district' in gdf_export.columns:
        print(f"  District names: {len(gdf_export['district'].unique())} unique")
    print(f"  Bounds: {gdf_export.total_bounds}")
    print(f"\n  Files created:")
    print(f"    1. {OUTPUT_FILE.relative_to(BASE_DIR)}")
    print(f"    2. {OUTPUT_SIMPLIFIED.relative_to(BASE_DIR)}")
    print(f"\n  Use simplified version for web maps for better performance.")
    print("=" * 70)

if __name__ == "__main__":
    main()
