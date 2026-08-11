#!/usr/bin/env python3
"""
Extract lithology data from all .mdb files.
Creates comprehensive litho.csv with rock descriptions and depth ranges.
"""
import subprocess
import os
import csv
import sys
from pathlib import Path

MDB_DIR = Path("GW_Data/Water Level")
OUTPUT_CSV = Path("data/litho.csv")

def get_mdb_files():
    """Get all .mdb files from GW_Data directory."""
    if not MDB_DIR.exists():
        print(f"Error: {MDB_DIR} not found")
        sys.exit(1)
    
    mdb_files = list(MDB_DIR.glob("*.mdb")) + list(MDB_DIR.glob("*.MDB"))
    print(f"Found {len(mdb_files)} .mdb files")
    return mdb_files

def extract_lithology(mdb_file):
    """Extract lithology data from a single .mdb file."""
    print(f"Processing: {mdb_file.name}")
    
    # Try different table names
    table_names = ["Well Lithology", "Lithology", "LITHOLOGY", "Well_Lithology"]
    
    for table_name in table_names:
        try:
            # Use mdb-export to extract table
            result = subprocess.run(
                ["mdb-export", str(mdb_file), table_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                # Successfully extracted table
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Has header + data
                    print(f"  ✓ Found {len(lines)-1} lithology records in '{table_name}'")
                    return lines
            
        except subprocess.TimeoutExpired:
            print(f"  ⚠ Timeout extracting from {mdb_file.name}")
            continue
        except Exception as e:
            print(f"  ⚠ Error with table '{table_name}': {e}")
            continue
    
    print(f"  ✗ No lithology data found in {mdb_file.name}")
    return None

def parse_lithology_row(row_dict):
    """Parse and normalize a lithology row."""
    # Normalize column names
    well_id = (row_dict.get('Well No') or 
               row_dict.get('Well_No') or 
               row_dict.get('WellNo') or 
               row_dict.get('WELL_NO') or '').strip().strip('"')
    
    depth_to = (row_dict.get('Depth To') or 
                row_dict.get('Depth_To') or 
                row_dict.get('DepthTo') or 
                row_dict.get('DEPTH_TO') or '').strip().strip('"')
    
    lithology = (row_dict.get('Lithology') or 
                 row_dict.get('LITHOLOGY') or 
                 row_dict.get('Litho') or '').strip().strip('"')
    
    colour = (row_dict.get('Colour') or 
              row_dict.get('Color') or 
              row_dict.get('COLOUR') or '').strip().strip('"')
    
    texture = (row_dict.get('Texture') or 
               row_dict.get('TEXTURE') or '').strip().strip('"')
    
    return {
        'well_id': well_id,
        'depth_to_m': depth_to,
        'lithology': lithology,
        'colour': colour,
        'texture': texture
    }

def main():
    """Main extraction process."""
    print("=" * 60)
    print("Extracting Lithology Data from .mdb Files")
    print("=" * 60)
    
    mdb_files = get_mdb_files()
    
    all_litho_records = []
    files_with_data = 0
    total_records = 0
    
    for mdb_file in mdb_files:
        csv_lines = extract_lithology(mdb_file)
        
        if csv_lines:
            files_with_data += 1
            
            # Parse CSV lines
            reader = csv.DictReader(csv_lines)
            for row in reader:
                parsed = parse_lithology_row(row)
                
                # Only keep if we have essential data
                if parsed['well_id'] and parsed['lithology']:
                    all_litho_records.append(parsed)
                    total_records += 1
    
    print(f"\n" + "=" * 60)
    print(f"Extraction Summary:")
    print(f"  Files processed: {len(mdb_files)}")
    print(f"  Files with lithology data: {files_with_data}")
    print(f"  Total lithology records: {total_records}")
    print("=" * 60)
    
    # Write to CSV
    if all_litho_records:
        OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['well_id', 'depth_to_m', 'lithology', 'colour', 'texture']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_litho_records)
        
        print(f"\n✓ Created: {OUTPUT_CSV}")
        print(f"  Total records: {total_records}")
        
        # Show sample
        print(f"\nSample records:")
        for i, record in enumerate(all_litho_records[:5]):
            print(f"  {i+1}. {record['well_id']}: {record['lithology']} @ {record['depth_to_m']}m")
        
        return 0
    else:
        print("\n✗ No lithology data extracted!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
