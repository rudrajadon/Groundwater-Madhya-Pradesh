#!/usr/bin/env python3
"""
Spatial join to assign wells to correct districts using district boundary polygons.
Updates the wells table in PostgreSQL with accurate district names.
"""
import geopandas as gpd
import psycopg2
from pathlib import Path
import sys
import argparse

# Paths
BASE_DIR = Path(__file__).parent.parent
SHP_PATH = BASE_DIR / "23" / "MP_DISTRICT_BDY.shp"

# Database
DATABASE_URL = "postgresql://gwuser:changeme@localhost:5432/groundwater"

def main(auto_confirm=False):
    print("=" * 70)
    print("Spatial Join: Assign Wells to Correct Districts")
    print("=" * 70)
    
    # 1. Load district boundaries
    print(f"\n[1/5] Loading district boundaries...")
    districts_gdf = gpd.read_file(SHP_PATH)
    districts_gdf = districts_gdf.to_crs("EPSG:4326")  # WGS84
    
    # Standardize district column
    districts_gdf = districts_gdf.rename(columns={'DISTRICT': 'district'})
    districts_gdf['district'] = districts_gdf['district'].astype(str).str.strip()
    
    print(f"  ✓ Loaded {len(districts_gdf)} districts")
    print(f"  ✓ CRS: {districts_gdf.crs}")
    
    # 2. Load wells from database
    print(f"\n[2/5] Loading wells from database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT well_id, 
               ST_Y(geom::geometry) as lat, 
               ST_X(geom::geometry) as lon,
               district as old_district
        FROM wells 
        WHERE geom IS NOT NULL
    """)
    
    wells_data = cur.fetchall()
    print(f"  ✓ Loaded {len(wells_data)} wells with coordinates")
    
    # Convert to GeoDataFrame
    import pandas as pd
    from shapely.geometry import Point
    
    wells_df = pd.DataFrame(wells_data, columns=['well_id', 'lat', 'lon', 'old_district'])
    wells_df['geometry'] = wells_df.apply(lambda row: Point(row['lon'], row['lat']), axis=1)
    wells_gdf = gpd.GeoDataFrame(wells_df, geometry='geometry', crs='EPSG:4326')
    
    print(f"  ✓ Created GeoDataFrame with {len(wells_gdf)} wells")
    
    # 3. Perform spatial join
    print(f"\n[3/5] Performing spatial join...")
    print(f"  This matches each well point to the district polygon it falls within...")
    
    # Spatial join: wells (points) to districts (polygons)
    wells_with_districts = gpd.sjoin(
        wells_gdf, 
        districts_gdf[['district', 'geometry']], 
        how='left',
        predicate='within'
    )
    
    # Handle wells that don't fall in any district (coastal/border issues)
    # Use nearest district for those
    unmatched = wells_with_districts['district'].isna()
    n_unmatched = unmatched.sum()
    
    if n_unmatched > 0:
        print(f"  ⚠ {n_unmatched} wells don't fall within any district polygon")
        print(f"    Using nearest district for these wells...")
        
        for idx in wells_with_districts[unmatched].index:
            well_point = wells_with_districts.loc[idx, 'geometry']
            # Find nearest district
            districts_gdf['distance'] = districts_gdf.geometry.distance(well_point)
            nearest_idx = districts_gdf['distance'].idxmin()
            nearest_district = districts_gdf.loc[nearest_idx, 'district']
            wells_with_districts.loc[idx, 'district'] = nearest_district
    
    print(f"  ✓ Spatial join complete")
    
    # 4. Compare old vs new assignments
    print(f"\n[4/5] Analyzing changes...")
    
    wells_with_districts['district_changed'] = (
        wells_with_districts['old_district'] != wells_with_districts['district']
    )
    
    n_changed = wells_with_districts['district_changed'].sum()
    n_total = len(wells_with_districts)
    pct_changed = (n_changed / n_total * 100) if n_total > 0 else 0
    
    print(f"  Total wells: {n_total}")
    print(f"  Changed: {n_changed} ({pct_changed:.1f}%)")
    print(f"  Unchanged: {n_total - n_changed} ({100-pct_changed:.1f}%)")
    
    if n_changed > 0:
        print(f"\n  Sample changes:")
        changes = wells_with_districts[wells_with_districts['district_changed']][
            ['well_id', 'old_district', 'district']
        ].head(10)
        for _, row in changes.iterrows():
            print(f"    {row['well_id']}: '{row['old_district']}' → '{row['district']}'")
    
    # Show district distribution
    print(f"\n  New district distribution:")
    dist_counts = wells_with_districts['district'].value_counts().head(10)
    for district, count in dist_counts.items():
        print(f"    {district:<20} : {count:>3} wells")
    
    # 5. Update database
    print(f"\n[5/5] Updating database...")
    
    if not auto_confirm:
        user_input = input(f"\n  Update {n_changed} wells in database? (yes/no): ").strip().lower()
        
        if user_input != 'yes':
            print(f"  ✗ Cancelled by user")
            cur.close()
            conn.close()
            sys.exit(0)
    else:
        print(f"  Auto-confirming update...")
    
    print(f"  Updating wells table...")
    
    updated = 0
    for _, row in wells_with_districts.iterrows():
        cur.execute("""
            UPDATE wells 
            SET district = %s 
            WHERE well_id = %s
        """, (row['district'], row['well_id']))
        updated += 1
        
        if updated % 100 == 0:
            print(f"    Updated {updated}/{n_total} wells...")
    
    conn.commit()
    print(f"  ✓ Updated {updated} wells")
    
    # Verify
    print(f"\n  Verifying update...")
    cur.execute("""
        SELECT district, COUNT(*) as count 
        FROM wells 
        WHERE geom IS NOT NULL 
        GROUP BY district 
        ORDER BY count DESC
        LIMIT 10
    """)
    
    print(f"\n  Top 10 districts by well count:")
    for district, count in cur.fetchall():
        print(f"    {district:<20} : {count:>3} wells")
    
    cur.close()
    conn.close()
    
    print(f"\n" + "=" * 70)
    print(f"✅ SUCCESS!")
    print(f"=" * 70)
    print(f"  Updated {n_changed} well districts using spatial join")
    print(f"  All {n_total} wells now have accurate district assignments")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fix well district assignments using spatial join')
    parser.add_argument('--yes', action='store_true', help='Auto-confirm database update')
    args = parser.parse_args()
    
    main(auto_confirm=args.yes)
