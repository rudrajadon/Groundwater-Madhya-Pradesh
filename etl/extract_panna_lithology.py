#!/usr/bin/env python3
"""
Extract lithology data from Panna MDB files and merge into litho.csv.
This will fix the 103 Unknown Panna wells by adding their missing lithology data.
"""
import pandas as pd
import subprocess
import re

def extract_mdb_lithology(mdb_file, table_name="Well Lithology"):
    """Extract lithology table from MDB file using mdb-export."""
    cmd = ['mdb-export', mdb_file, table_name]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    # Parse CSV output
    from io import StringIO
    df = pd.read_csv(StringIO(result.stdout))
    return df

def standardize_well_id(well_id):
    """Standardize well ID to match our format: UPPERCASE, no spaces, 0W→OW."""
    if pd.isna(well_id):
        return well_id
    
    wid = str(well_id).strip().upper()
    
    # Remove spaces
    wid = wid.replace(' ', '')
    
    # Fix 0W → OW
    wid = re.sub(r'-0W$', '-OW', wid)
    wid = re.sub(r'-0W-', '-OW-', wid)
    
    # Handle Panna-PZ-01 → PANNA-PZ-01
    wid = wid.replace('PANNA-PZ-', 'PANNA-PZ-')
    
    return wid

def extract_panna_data():
    """Extract and merge Panna lithology data."""
    print("=" * 70)
    print("EXTRACTING PANNA LITHOLOGY DATA")
    print("=" * 70)
    
    # 1. Extract from both Panna MDB files
    print("\n1. Extracting from Spannaow.Mdb (observation wells)...")
    panna_ow = extract_mdb_lithology('GW_Data/Water Level/Spannaow.Mdb')
    print(f"   Extracted {len(panna_ow)} records from {panna_ow['Well No'].nunique()} wells")
    
    print("\n2. Extracting from sPannaPZ.mdb (piezometers)...")
    panna_pz = extract_mdb_lithology('GW_Data/Water Level/sPannaPZ.mdb')
    print(f"   Extracted {len(panna_pz)} records from {panna_pz['Well No'].nunique()} wells")
    
    # 2. Combine both datasets
    print("\n3. Combining datasets...")
    
    # Standardize column names
    panna_ow_clean = pd.DataFrame({
        'well_id': panna_ow['Well No'].apply(standardize_well_id),
        'depth_to_m': pd.to_numeric(panna_ow['Depth To'], errors='coerce'),
        'lithology': panna_ow['Lithology'],
        'colour': panna_ow['Colour'],
        'texture': panna_ow['Texture']
    })
    
    panna_pz_clean = pd.DataFrame({
        'well_id': panna_pz['Well No'].apply(standardize_well_id),
        'depth_to_m': pd.to_numeric(panna_pz['Depth To'], errors='coerce'),
        'lithology': panna_pz['Lithology'],
        'colour': panna_pz['Colour'],
        'texture': panna_pz['Texture']
    })
    
    # Combine
    panna_all = pd.concat([panna_ow_clean, panna_pz_clean], ignore_index=True)
    
    # Remove rows with missing critical data
    panna_all = panna_all.dropna(subset=['well_id', 'lithology'])
    
    print(f"   Combined: {len(panna_all)} records from {panna_all['well_id'].nunique()} wells")
    
    # 3. Load existing litho.csv
    print("\n4. Loading existing litho.csv...")
    litho_existing = pd.read_csv('data/litho.csv')
    print(f"   Existing records: {len(litho_existing)}")
    print(f"   Existing Panna wells: {litho_existing['well_id'].str.contains('PANNA', na=False).sum()}")
    
    # 4. Remove old Panna records (to avoid duplicates)
    litho_no_panna = litho_existing[~litho_existing['well_id'].str.contains('PANNA', case=False, na=False)]
    print(f"\n5. Removing old Panna records...")
    print(f"   Records after removal: {len(litho_no_panna)}")
    
    # 5. Merge new Panna data
    print("\n6. Merging new Panna lithology...")
    litho_updated = pd.concat([litho_no_panna, panna_all], ignore_index=True)
    print(f"   Total records: {len(litho_updated)}")
    print(f"   Panna wells now: {litho_updated['well_id'].str.contains('PANNA', na=False).sum()}")
    
    # 6. Show sample of new data
    print("\n7. Sample Panna lithology data:")
    panna_sample = panna_all.groupby('well_id').first().head(10)
    for well_id, row in panna_sample.iterrows():
        print(f"   {well_id:20} {row['depth_to_m']:6.1f}m: {row['lithology']}")
    
    # 7. Save updated litho.csv
    print("\n8. Saving updated litho.csv...")
    litho_updated.to_csv('data/litho.csv', index=False)
    print("   ✅ Saved!")
    
    # 8. Statistics on geology keywords
    print("\n9. Analyzing geology types in new Panna data...")
    panna_litho_text = ' '.join(panna_all['lithology'].astype(str).str.lower())
    
    granite_count = sum(1 for kw in ['granite', 'gneiss', 'crystalline', 'hard rock'] if kw in panna_litho_text)
    sandstone_count = sum(1 for kw in ['sandstone', 'shale', 'limestone', 'sediment'] if kw in panna_litho_text)
    
    print(f"   Granite keywords found: {granite_count > 0}")
    print(f"   Vindhyan keywords found: {sandstone_count > 0}")
    
    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE!")
    print("=" * 70)
    print("\nNext step: Re-run fix_data_quality.py to classify the new Panna wells")
    
    return litho_updated

if __name__ == "__main__":
    import sys
    try:
        extract_panna_data()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
