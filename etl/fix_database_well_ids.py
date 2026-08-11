#!/usr/bin/env python3
"""
Fix well_id formatting in database (0W → OW) and update geology classifications.
This syncs the database with the corrected CSV data.
"""
import psycopg2
import pandas as pd

def fix_database_well_ids():
    print("=" * 70)
    print("FIXING DATABASE WELL IDs (0W → OW)")
    print("=" * 70)
    
    # Load correct classifications from CSV
    print("\n1. Loading correct classifications from CSV...")
    class_df = pd.read_csv('data/well_geology_classifications.csv')
    print(f"   Loaded {len(class_df)} classifications")
    
    # Connect to database
    print("\n2. Connecting to database...")
    conn = psycopg2.connect("postgresql://gwuser:changeme@localhost:5432/groundwater")
    cur = conn.cursor()
    
    # Find wells with '0W' format in database
    print("\n3. Finding wells with '0W' format...")
    cur.execute("SELECT well_id FROM wells WHERE well_id LIKE '%0W%'")
    old_format_wells = [row[0] for row in cur.fetchall()]
    print(f"   Found {len(old_format_wells)} wells with '0W' format:")
    for wid in old_format_wells:
        print(f"     {wid}")
    
    if not old_format_wells:
        print("\n   No wells to fix!")
        cur.close()
        conn.close()
        return 0
    
    # Fix each well
    print("\n4. Fixing well IDs (CASCADE constraint now enabled)...")
    fixed_count = 0
    
    for old_well_id in old_format_wells:
        # Generate new well_id (0W → OW)
        new_well_id = old_well_id.replace('-0W', '-OW')
        
        # Get correct geology from CSV
        well_data = class_df[class_df['well_id'] == new_well_id]
        
        if len(well_data) == 0:
            print(f"   ⚠️  {old_well_id} → {new_well_id}: NOT FOUND in CSV, skipping")
            continue
        
        geology_type = well_data.iloc[0]['geology_type']
        aquifer_class = well_data.iloc[0]['aquifer_classification']
        
        try:
            # Update wells table (CASCADE will update readings automatically)
            cur.execute("""
                UPDATE wells 
                SET well_id = %s, 
                    geology_type = %s,
                    aquifer_classification = %s
                WHERE well_id = %s
            """, (new_well_id, geology_type, aquifer_class, old_well_id))
            
            # Check how many readings were affected
            cur.execute("SELECT COUNT(*) FROM readings WHERE well_id = %s", (new_well_id,))
            readings_count = cur.fetchone()[0]
            
            print(f"   ✓ {old_well_id:20} → {new_well_id:20} ({geology_type:12}, {aquifer_class:12}) [{readings_count} readings]")
            fixed_count += 1
            
        except Exception as e:
            print(f"   ❌ {old_well_id} → {new_well_id}: {e}")
    
    # Commit all changes
    conn.commit()
    print(f"\n5. Committed {fixed_count} updates")
    
    # Verify
    print("\n6. Verification - checking for remaining '0W' wells...")
    cur.execute("SELECT well_id FROM wells WHERE well_id LIKE '%0W%'")
    remaining = cur.fetchall()
    
    if remaining:
        print(f"   ⚠️  {len(remaining)} wells still have '0W' format:")
        for row in remaining:
            print(f"     {row[0]}")
    else:
        print("   ✓ All wells now use 'OW' format!")
    
    # Check Unknown count
    print("\n7. Unknown geology count:")
    cur.execute("SELECT COUNT(*) FROM wells WHERE geology_type = 'Unknown'")
    unknown_count = cur.fetchone()[0]
    print(f"   Unknown: {unknown_count} wells")
    
    # Panna Unknown count
    cur.execute("SELECT COUNT(*) FROM wells WHERE well_id LIKE 'PANNA%' AND geology_type = 'Unknown'")
    panna_unknown = cur.fetchone()[0]
    print(f"   Panna Unknown: {panna_unknown} wells")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("✓ DATABASE WELL IDs FIXED!")
    print("=" * 70)
    
    return fixed_count

if __name__ == "__main__":
    import sys
    try:
        fixed = fix_database_well_ids()
        print(f"\n✅ Fixed {fixed} well IDs")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
