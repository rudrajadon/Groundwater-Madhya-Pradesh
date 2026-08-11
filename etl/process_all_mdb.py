"""
Process ALL MDB files from GW_Data directory and load into PostgreSQL.

This script:
1. Finds all .mdb/.MDB files in GW_Data/Water Level and GW_Data/Water Quality
2. Exports each to CSV using mdb-tools
3. Loads wells, readings, and water quality data into PostgreSQL
4. Handles different naming conventions and table structures across files

Usage:
    export DATABASE_URL=postgresql://user:pass@localhost:5432/groundwater
    python process_all_mdb.py --data-dir ../GW_Data --csv-output ./raw_csv_all
"""
import argparse
import os
import sys
import subprocess
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from parse_coordinates import parse_and_validate

# District/location name extraction from filename
DISTRICT_MAP = {
    'indore': 'Indore',
    'ujjan': 'Ujjain',
    'jbp': 'Jabalpur',
    'bhopal': 'Bhopal',
    'stn': 'Satna',
    'guna': 'Guna',
    'sagar': 'Sagar',
    'panna': 'Panna',
    'chhat': 'Chhatarpur',
    'tkm': 'Tikamgarh',
    'sgr': 'Sagar',
}

def extract_district_from_filename(filename: str) -> str:
    """Extract district name from MDB filename."""
    fname = filename.lower().replace('.mdb', '')
    for key, district in DISTRICT_MAP.items():
        if key in fname:
            return district
    return 'Unknown'

def get_well_type_from_filename(filename: str) -> str:
    """Determine well type (OW=observation well, PZ=piezometer) from filename."""
    fname = filename.upper()
    if 'PZ' in fname:
        return 'Piezometer'
    elif 'OW' in fname or 'POW' in fname:
        return 'Observation Well'
    return 'Unknown'

def export_mdb_to_csv(mdb_path: str, output_dir: str) -> dict:
    """
    Export all tables from an MDB file to CSV files.
    Returns dict mapping table names to CSV paths.
    """
    mdb_name = Path(mdb_path).stem
    out_subdir = Path(output_dir) / mdb_name
    out_subdir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Processing: {mdb_path}")
    print(f"Output dir: {out_subdir}")
    
    # Get list of tables
    try:
        result = subprocess.run(
            ['mdb-tables', '-1', mdb_path],
            capture_output=True,
            text=True,
            check=True
        )
        tables = [t.strip() for t in result.stdout.strip().split('\n') if t.strip()]
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Could not read tables from {mdb_path}: {e}")
        return {}
    except FileNotFoundError:
        print("ERROR: mdb-tools not found. Install with: brew install mdbtools")
        sys.exit(1)
    
    # Filter out system tables
    tables = [t for t in tables if not t.startswith('MSys')]
    print(f"Found {len(tables)} user tables: {tables}")
    
    # Export each table
    csv_paths = {}
    for table in tables:
        safe_name = table.replace(' ', '_').replace('/', '_').replace('-', '_')
        csv_path = out_subdir / f"{safe_name}.csv"
        try:
            with open(csv_path, 'w') as f:
                subprocess.run(
                    ['mdb-export', mdb_path, table],
                    stdout=f,
                    check=True,
                    text=True
                )
            csv_paths[table] = str(csv_path)
            print(f"  ✓ {table} -> {csv_path.name}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed to export {table}: {e}")
    
    return csv_paths

def find_table_by_keywords(csv_paths: dict, keywords: list[str]) -> str | None:
    """Find a table name that contains any of the keywords (case-insensitive)."""
    for table_name in csv_paths.keys():
        for keyword in keywords:
            if keyword.lower() in table_name.lower():
                return table_name
    return None

def load_wells_from_csv(conn, csv_path: str, district: str, well_type: str, source_file: str):
    """Load well master data from a CSV file."""
    if not os.path.exists(csv_path):
        print(f"  [skip] Wells CSV not found: {csv_path}")
        return 0
    
    df = pd.read_csv(csv_path)
    print(f"  Wells CSV columns: {list(df.columns)}")
    
    # Common column name variations
    well_id_cols = ['Well No', 'WellNo', 'Well_No', 'WELL_NO', 'Well no']
    lat_cols = ['Latitude', 'Lat', 'LAT']
    lon_cols = ['Longitude', 'Long', 'LON', 'Lon']
    elevation_cols = ['Elevation of Ground Level', 'Elevation', 'GL', 'RL']
    tahsil_cols = ['Tahsil / Taluk', 'Tahsil', 'Taluk', 'TAHSIL']
    block_cols = ['Block / Mandal', 'Block', 'BLOCK']
    village_cols = ['Village', 'VILLAGE']
    
    # Find actual column names
    well_id_col = next((c for c in well_id_cols if c in df.columns), None)
    lat_col = next((c for c in lat_cols if c in df.columns), None)
    lon_col = next((c for c in lon_cols if c in df.columns), None)
    elevation_col = next((c for c in elevation_cols if c in df.columns), None)
    tahsil_col = next((c for c in tahsil_cols if c in df.columns), None)
    block_col = next((c for c in block_cols if c in df.columns), None)
    village_col = next((c for c in village_cols if c in df.columns), None)
    
    if not well_id_col:
        print(f"  [skip] No well ID column found in {csv_path}")
        return 0
    
    rows = []
    n_invalid = 0
    for _, r in df.iterrows():
        well_id = str(r.get(well_id_col, '')).strip()
        if not well_id or well_id.lower() in ['nan', '', 'none']:
            continue
        
        # Parse coordinates if available
        lat_raw = str(r.get(lat_col, '') or '') if lat_col else ''
        lon_raw = str(r.get(lon_col, '') or '') if lon_col else ''
        
        lat, lon, coord_valid = None, None, False
        if lat_raw and lon_raw:
            coord = parse_and_validate(lat_raw, lon_raw)
            lat, lon, coord_valid = coord.lat, coord.lon, coord.valid
            if not coord_valid:
                n_invalid += 1
        
        # Get other fields
        elevation = r.get(elevation_col) if elevation_col else None
        if elevation is not None and not pd.isna(elevation):
            try:
                elevation = float(elevation)
            except:
                elevation = None
        else:
            elevation = None
        
        tahsil = r.get(tahsil_col) if tahsil_col else None
        block = r.get(block_col) if block_col else None
        village = r.get(village_col) if village_col else None
        
        # Build geom or None
        geom_val = f"SRID=4326;POINT({lon} {lat})" if (lon is not None and lat is not None) else None
        
        rows.append((
            well_id,
            well_type,
            None,  # agency
            district,
            tahsil,
            block,
            village,
            geom_val,  # WKT format or None
            lat_raw, lon_raw,
            coord_valid,
            elevation,
            None,  # command_area
            source_file
        ))
    
    if rows:
        print(f"  Debug: Loading {len(rows)} wells")
        with conn.cursor() as cur:
            execute_values(cur, """
                INSERT INTO wells (
                    well_id, well_type, agency, district, tahsil,
                    block, village, geom, lat_raw, lon_raw, coord_validated,
                    elevation_m, command_area, source_file
                )
                VALUES %s
                ON CONFLICT (well_id) DO UPDATE SET
                    geom = EXCLUDED.geom,
                    coord_validated = EXCLUDED.coord_validated,
                    district = COALESCE(EXCLUDED.district, wells.district),
                    tahsil = COALESCE(EXCLUDED.tahsil, wells.tahsil),
                    elevation_m = COALESCE(EXCLUDED.elevation_m, wells.elevation_m),
                    source_file = EXCLUDED.source_file
            """, rows, template="(%s, %s, %s, %s, %s, %s, %s, %s::geography, %s, %s, %s, %s, %s, %s)")
        conn.commit()
        print(f"  ✓ Loaded {len(rows)} wells ({n_invalid} with unvalidated coordinates)")
    
    return len(rows)

def load_readings_from_csv(conn, csv_path: str, source_file: str):
    """Load water level readings from a CSV file."""
    if not os.path.exists(csv_path):
        print(f"  [skip] Readings CSV not found: {csv_path}")
        return 0
    
    df = pd.read_csv(csv_path)
    print(f"  Readings CSV columns: {list(df.columns)}")
    
    # Common column name variations
    well_id_cols = ['Well No', 'WellNo', 'Well_No', 'WELL_NO', 'Well no']
    date_cols = ['Date', 'DATE', 'date', 'Date of obs', 'Date of Observation']
    depth_cols = ['Water Level', 'WL', 'Depth', 'PW-SWL', 'SWL', 'DTW', 'Depth to Water Level']
    
    # Find actual columns
    well_id_col = next((c for c in well_id_cols if c in df.columns), None)
    date_col = next((c for c in date_cols if c in df.columns), None)
    
    # Find depth column - may need to check multiple piezometer/well columns
    depth_col = next((c for c in depth_cols if c in df.columns), None)
    if not depth_col:
        # Look for any column with 'SWL' or 'WL' in it
        depth_col = next((c for c in df.columns if 'SWL' in c.upper() or c.upper() == 'WL'), None)
    
    if not well_id_col or not date_col:
        print(f"  [skip] Required columns not found (well_id: {well_id_col}, date: {date_col})")
        return 0
    
    if not depth_col:
        print(f"  [warning] No depth column found, trying first numeric column after date")
        # Try to find first numeric column
        for col in df.columns:
            if col not in [well_id_col, date_col] and pd.api.types.is_numeric_dtype(df[col]):
                depth_col = col
                print(f"  Using column: {depth_col}")
                break
    
    if not depth_col:
        print(f"  [skip] No depth column found")
        return 0
    
    # Parse dates
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    # Get elevation data for head_msl computation
    with conn.cursor() as cur:
        cur.execute("SELECT well_id, elevation_m FROM wells")
        elevations = dict(cur.fetchall())
    
    rows = []
    for _, r in df.iterrows():
        well_id = str(r.get(well_id_col, '')).strip()
        depth = r.get(depth_col)
        
        if not well_id or well_id.lower() in ['nan', '', 'none']:
            continue
        if pd.isna(depth):
            continue
        
        try:
            depth_val = float(depth)
            # Skip obviously invalid values (negative depth or > 300m)
            if depth_val < 0 or depth_val > 300:
                continue
        except (ValueError, TypeError):
            continue
        
        # Compute head_msl if elevation is known
        elev = elevations.get(well_id)
        head_msl = (float(elev) - depth_val) if elev is not None else None
        
        rows.append((
            well_id,
            r[date_col].date(),
            depth_val,
            head_msl,
            source_file
        ))
    
    if not rows:
        print(f"  [skip] No valid readings found")
        return 0
    
    # Deduplicate: keep last occurrence for each (well_id, date)
    seen = {}
    for row in rows:
        seen[(row[0], row[1])] = row
    rows = list(seen.values())
    
    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO readings (well_id, date, depth_bgl_m, head_msl_m, source)
            VALUES %s
            ON CONFLICT (well_id, date) DO UPDATE SET
                depth_bgl_m = EXCLUDED.depth_bgl_m,
                head_msl_m = EXCLUDED.head_msl_m,
                source = EXCLUDED.source
        """, rows)
    conn.commit()
    
    print(f"  ✓ Loaded {len(rows)} readings")
    return len(rows)

def process_water_level_mdb(conn, mdb_path: str, csv_output_dir: str):
    """Process a single water level MDB file."""
    filename = Path(mdb_path).name
    district = extract_district_from_filename(filename)
    well_type = get_well_type_from_filename(filename)
    
    print(f"\n{'='*60}")
    print(f"Processing Water Level: {filename}")
    print(f"  District: {district}, Type: {well_type}")
    
    try:
        # Export to CSV
        csv_paths = export_mdb_to_csv(mdb_path, csv_output_dir)
        if not csv_paths:
            return
        
        # Find wells table (GroundWater-General, Master, etc.)
        wells_table = find_table_by_keywords(csv_paths, [
            'GroundWater-General', 'GroundWater', 'Master', 'General'
        ])
        
        # Find readings table - prefer "Water Levels" over APT-Data
        readings_table = find_table_by_keywords(csv_paths, [
            'Water Levels', 'Water Level', 'Water_Levels'
        ])
        
        print(f"  Identified tables - Wells: {wells_table}, Readings: {readings_table}")
        
        # Load wells
        if wells_table:
            load_wells_from_csv(conn, csv_paths[wells_table], district, well_type, filename)
        
        # Load readings
        if readings_table:
            load_readings_from_csv(conn, csv_paths[readings_table], filename)
    except Exception as e:
        print(f"ERROR processing {filename}: {e}")
        conn.rollback()  # Rollback on error to allow next file to proceed
        import traceback
        traceback.print_exc()

def process_all_water_level_files(conn, data_dir: str, csv_output_dir: str):
    """Process all water level MDB files."""
    wl_dir = Path(data_dir) / 'Water Level'
    if not wl_dir.exists():
        print(f"ERROR: Water Level directory not found: {wl_dir}")
        return
    
    mdb_files = list(wl_dir.glob('*.mdb')) + list(wl_dir.glob('*.MDB')) + list(wl_dir.glob('*.Mdb'))
    print(f"\nFound {len(mdb_files)} water level MDB files")
    
    total_wells = 0
    total_readings = 0
    
    for mdb_path in sorted(mdb_files):
        try:
            process_water_level_mdb(conn, str(mdb_path), csv_output_dir)
        except Exception as e:
            print(f"ERROR processing {mdb_path.name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Get final counts
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM wells")
        total_wells = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM readings")
        total_readings = cur.fetchone()[0]
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_wells} wells, {total_readings} readings in database")

def main():
    ap = argparse.ArgumentParser(description='Process all MDB files from GW_Data directory')
    ap.add_argument('--data-dir', required=True, help='Path to GW_Data directory')
    ap.add_argument('--csv-output', default='./raw_csv_all', help='Output directory for CSV files')
    args = ap.parse_args()
    
    # Check mdb-tools
    try:
        subprocess.run(['mdb-tables', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: mdb-tools not found. Install with: brew install mdbtools")
        sys.exit(1)
    
    # Database connection
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: Set DATABASE_URL environment variable")
        print("Example: export DATABASE_URL=postgresql://user:pass@localhost:5432/groundwater")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        print(f"✓ Connected to database")
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)
    
    # Add source_file column if it doesn't exist
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE wells 
            ADD COLUMN IF NOT EXISTS source_file TEXT;
        """)
        conn.commit()
    
    # Process all files
    process_all_water_level_files(conn, args.data_dir, args.csv_output)
    
    conn.close()
    print("\n✓ All done!")

if __name__ == '__main__':
    main()
