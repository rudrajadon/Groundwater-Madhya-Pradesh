"""
Create a strategic subset of wells for faster training.

Selection criteria:
- Wells with >= 24 months of data
- Valid coordinates
- Representative distribution across districts
- Mix of observation wells and piezometers
- Prioritize recent data (post-2000)
"""
import os
import sys
import psycopg2
import pandas as pd
from collections import defaultdict

def select_subset_wells(conn, target_count=300, min_readings=24):
    """Select best wells for training subset."""
    
    # Get well statistics
    query = """
    WITH well_stats AS (
        SELECT 
            w.well_id,
            w.well_type,
            w.district,
            COUNT(r.id) as reading_count,
            MIN(r.date) as first_reading,
            MAX(r.date) as last_reading,
            AVG(r.depth_bgl_m) as avg_depth,
            STDDEV(r.depth_bgl_m) as depth_stddev,
            w.elevation_m,
            w.coord_validated,
            ST_Y(w.geom::geometry) as latitude,
            ST_X(w.geom::geometry) as longitude
        FROM wells w
        JOIN readings r ON w.well_id = r.well_id
        WHERE w.geom IS NOT NULL
          AND r.depth_bgl_m IS NOT NULL
          AND r.depth_bgl_m > 0
          AND r.depth_bgl_m < 300
          AND r.date >= '1990-01-01'  -- Focus on modern data
          AND r.date <= '2025-12-31'  -- Exclude obvious errors
        GROUP BY w.well_id, w.well_type, w.district, w.elevation_m, w.coord_validated, w.geom
    )
    SELECT *,
           EXTRACT(YEAR FROM last_reading) - EXTRACT(YEAR FROM first_reading) as years_span
    FROM well_stats
    WHERE reading_count >= %s
      AND elevation_m IS NOT NULL
      AND depth_stddev > 0.5  -- Some variation (not flat line)
    ORDER BY 
        reading_count DESC,
        years_span DESC
    """
    
    df = pd.read_sql(query, conn, params=(min_readings,))
    print(f"✓ Found {len(df)} wells with >= {min_readings} readings")
    
    # Distribute across districts
    selected = []
    wells_per_district = defaultdict(int)
    target_per_district = target_count // len(df['district'].unique())
    
    # First pass: ensure each district gets representation
    for district in df['district'].unique():
        district_wells = df[df['district'] == district].head(target_per_district)
        selected.extend(district_wells['well_id'].tolist())
        wells_per_district[district] = len(district_wells)
        print(f"  {district}: {len(district_wells)} wells")
    
    # Second pass: fill remaining slots with best wells
    remaining = target_count - len(selected)
    if remaining > 0:
        already_selected = set(selected)
        additional = df[~df['well_id'].isin(already_selected)].head(remaining)
        selected.extend(additional['well_id'].tolist())
        print(f"  + {len(additional)} additional wells (best overall)")
    
    print(f"\n✓ Selected {len(selected)} wells total")
    
    # Stats
    selected_df = df[df['well_id'].isin(selected)]
    print(f"  Average readings per well: {selected_df['reading_count'].mean():.0f}")
    print(f"  Total readings: {selected_df['reading_count'].sum()}")
    print(f"  Date range: {selected_df['first_reading'].min()} to {selected_df['last_reading'].max()}")
    
    return selected

def export_subset(conn, well_ids, output_dir):
    """Export subset to CSV files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create SQL list
    well_list = ", ".join([f"'{w}'" for w in well_ids])
    
    # Export wells
    query_wells = f"""
        SELECT 
            well_id as "Well No",
            well_type as "Well Type",
            district as "District",
            tahsil as "Tahsil / Taluk",
            block as "Block / Mandal",
            village as "Village",
            ST_Y(geom::geometry) as "Northing",
            ST_X(geom::geometry) as "Easting",
            elevation_m as "Elevation of Ground Level",
            aquifer_zone as "Aquifer Zone",
            command_area as "Command Area",
            coord_validated as "Coord Validated"
        FROM wells
        WHERE well_id IN ({well_list})
        ORDER BY well_id
    """
    wells_df = pd.read_sql(query_wells, conn)
    wells_path = os.path.join(output_dir, 'wells.csv')
    wells_df.to_csv(wells_path, index=False)
    print(f"✓ Exported {len(wells_df)} wells to {wells_path}")
    
    # Export readings
    query_readings = f"""
        SELECT 
            r.well_id as "Well No",
            TO_CHAR(r.date, 'MM/DD/YY HH24:MI:SS') as "date",
            r.depth_bgl_m as "Water Level",
            r.head_msl_m,
            w.elevation_m,
            ST_Y(w.geom::geometry) as latitude,
            ST_X(w.geom::geometry) as longitude
        FROM readings r
        JOIN wells w ON r.well_id = w.well_id
        WHERE r.well_id IN ({well_list})
          AND r.depth_bgl_m IS NOT NULL
          AND r.depth_bgl_m > 0
          AND r.depth_bgl_m < 300
          AND r.date >= '1990-01-01'
          AND r.date <= '2025-12-31'
        ORDER BY r.well_id, r.date
    """
    readings_df = pd.read_sql(query_readings, conn)
    readings_path = os.path.join(output_dir, 'water_levels.csv')
    readings_df.to_csv(readings_path, index=False)
    print(f"✓ Exported {len(readings_df)} readings to {readings_path}")
    
    # Create empty litho file
    litho_path = os.path.join(output_dir, 'litho.csv')
    pd.DataFrame(columns=["Well_No", "Depth To", "Lithology", "Colour", "Texture"]).to_csv(litho_path, index=False)
    print(f"✓ Created empty {litho_path}")
    
    return len(wells_df), len(readings_df)

def main():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: Set DATABASE_URL environment variable")
        sys.exit(1)
    
    conn = psycopg2.connect(db_url)
    print("✓ Connected to database\n")
    
    print("Selecting strategic subset of wells...")
    well_ids = select_subset_wells(conn, target_count=300, min_readings=24)
    
    print("\nExporting subset to data/subset/...")
    n_wells, n_readings = export_subset(conn, well_ids, '../data/subset')
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Subset created successfully!")
    print(f"  Wells: {n_wells}")
    print(f"  Readings: {n_readings}")
    print(f"  Location: data/subset/")
    print(f"{'='*60}")
    print(f"\nNow train with:")
    print(f"  cd ../ml")
    print(f"  python train.py --data-dir ../data/subset --save-dir ./artifacts")

if __name__ == '__main__':
    main()
