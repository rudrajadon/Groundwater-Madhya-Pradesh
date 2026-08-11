"""
Export data from PostgreSQL to CSV files for ML training.

This script exports wells, readings, and lithology data from the database
to CSV files that the ML training script expects.

Usage:
    export DATABASE_URL=postgresql://gwuser:changeme@localhost:5432/groundwater
    python export_to_csv.py --output-dir ../data
"""
import argparse
import os
import sys
import psycopg2
import pandas as pd

def export_wells(conn, output_dir: str):
    """Export wells table to CSV."""
    query = """
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
        WHERE geom IS NOT NULL
        ORDER BY well_id
    """
    df = pd.read_sql(query, conn)
    output_path = os.path.join(output_dir, 'wells.csv')
    df.to_csv(output_path, index=False)
    print(f"✓ Exported {len(df)} wells to {output_path}")
    return len(df)

def export_readings(conn, output_dir: str):
    """Export readings table to CSV."""
    query = """
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
        WHERE w.geom IS NOT NULL
          AND r.depth_bgl_m IS NOT NULL
          AND r.depth_bgl_m > 0
          AND r.depth_bgl_m < 300
        ORDER BY r.well_id, r.date
    """
    df = pd.read_sql(query, conn)
    output_path = os.path.join(output_dir, 'water_levels.csv')
    df.to_csv(output_path, index=False)
    print(f"✓ Exported {len(df)} readings to {output_path}")
    return len(df)

def export_lithology(conn, output_dir: str):
    """Export lithology logs to CSV."""
    query = """
        SELECT 
            well_id as "Well_No",
            depth_to_m as "Depth To",
            lithology as "Lithology",
            colour as "Colour",
            texture as "Texture"
        FROM lithology_logs
        ORDER BY well_id, depth_to_m
    """
    df = pd.read_sql(query, conn)
    
    if len(df) > 0:
        output_path = os.path.join(output_dir, 'litho.csv')
        df.to_csv(output_path, index=False)
        print(f"✓ Exported {len(df)} lithology records to {output_path}")
    else:
        # Create empty litho file with correct columns
        output_path = os.path.join(output_dir, 'litho.csv')
        pd.DataFrame(columns=["Well_No", "Depth To", "Lithology", "Colour", "Texture"]).to_csv(output_path, index=False)
        print("⚠ No lithology data found - created empty litho.csv")
    
    return len(df)

def main():
    ap = argparse.ArgumentParser(description='Export database to CSV files for ML training')
    ap.add_argument('--output-dir', default='../data', help='Output directory for CSV files')
    args = ap.parse_args()
    
    # Database connection
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: Set DATABASE_URL environment variable")
        print("Example: export DATABASE_URL=postgresql://gwuser:changeme@localhost:5432/groundwater")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        print(f"✓ Connected to database")
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Export data
    print(f"\nExporting data to {args.output_dir}...")
    n_wells = export_wells(conn, args.output_dir)
    n_readings = export_readings(conn, args.output_dir)
    n_litho = export_lithology(conn, args.output_dir)
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Export complete!")
    print(f"  Wells: {n_wells}")
    print(f"  Readings: {n_readings}")
    print(f"  Lithology records: {n_litho}")
    print(f"{'='*60}")
    print(f"\nNow run the ML training with:")
    print(f"  cd ../ml")
    print(f"  python train.py --data-dir ../data --save-dir ./artifacts")

if __name__ == '__main__':
    main()
