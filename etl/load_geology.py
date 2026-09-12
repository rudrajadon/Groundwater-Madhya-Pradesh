#!/usr/bin/env python3
"""Load geology and aquifer classifications into wells table."""
import pandas as pd
import psycopg2

DATABASE_URL = "postgresql://gwuser:changeme@localhost:5432/groundwater"

def main():
    print("Loading geology classifications...")
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "well_geology_classifications.csv")
    df = pd.read_csv(data_path)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    updated = 0
    for _, row in df.iterrows():
        cur.execute("""
            UPDATE wells 
            SET geology_type = %s,
                aquifer_classification = %s
            WHERE well_id = %s
        """, (row['geology_type'], row['aquifer_classification'], row['well_id']))
        updated += 1
        
        if updated % 100 == 0:
            print(f"  Updated {updated}/{len(df)} wells...")
    
    conn.commit()
    print(f"✓ Updated {updated} wells with geology/aquifer data")
    
    # Update aquifer_zone to combine geology + aquifer
    cur.execute("""
        UPDATE wells 
        SET aquifer_zone = CONCAT(geology_type, ' - ', aquifer_classification)
        WHERE geology_type IS NOT NULL 
          AND aquifer_classification IS NOT NULL
    """)
    conn.commit()
    
    print(f"✓ Updated aquifer_zone column")
    
    # Verify
    cur.execute("""
        SELECT geology_type, aquifer_classification, COUNT(*) 
        FROM wells 
        WHERE geology_type IS NOT NULL
        GROUP BY geology_type, aquifer_classification
        ORDER BY COUNT(*) DESC
    """)
    
    print("\nGeology/Aquifer distribution:")
    for geology, aquifer, count in cur.fetchall():
        print(f"  {geology:<15} | {aquifer:<15} : {count:>3} wells")
    
    cur.close()
    conn.close()
    
    print("\n✅ Geology data loaded successfully!")

if __name__ == "__main__":
    main()
