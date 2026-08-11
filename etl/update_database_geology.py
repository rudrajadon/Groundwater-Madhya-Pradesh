#!/usr/bin/env python3
"""
Update database wells table with geology classifications.
"""
import pandas as pd
import psycopg2

def main():
    print("=" * 60)
    print("Updating Database with Geology Classifications")
    print("=" * 60)
    
    # Load classifications
    print("\n1. Loading classifications...")
    class_df = pd.read_csv('data/well_geology_classifications.csv')
    print(f"   Wells to update: {len(class_df)}")
    
    # Connect to database
    print("\n2. Connecting to database...")
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='groundwater',
        user='gwuser',
        password='changeme'
    )
    cur = conn.cursor()
    
    # Update each well
    print("\n3. Updating wells...")
    updated = 0
    for idx, row in class_df.iterrows():
        cur.execute("""
            UPDATE wells 
            SET geology_type = %s,
                aquifer_classification = %s
            WHERE well_id = %s
        """, (row['geology_type'], row['aquifer_classification'], row['well_id']))
        updated += cur.rowcount
        
        if (idx + 1) % 200 == 0:
            print(f"   Updated {idx + 1}/{len(class_df)} wells...")
    
    conn.commit()
    print(f"   ✓ Updated {updated} wells")
    
    # Verify
    print("\n4. Verification:")
    cur.execute("""
        SELECT 
            geology_type,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
        FROM wells
        WHERE geology_type IS NOT NULL
        GROUP BY geology_type
        ORDER BY count DESC
    """)
    
    print("\n   Geology Type Distribution in Database:")
    for row in cur.fetchall():
        print(f"     {row[0]:12} {row[1]:4} wells ({row[2]:5.1f}%)")
    
    cur.execute("""
        SELECT 
            aquifer_classification,
            COUNT(*) as count
        FROM wells
        WHERE aquifer_classification IS NOT NULL
        GROUP BY aquifer_classification
        ORDER BY count DESC
    """)
    
    print("\n   Aquifer Classification Distribution:")
    for row in cur.fetchall():
        print(f"     {row[0]:12} {row[1]:4} wells")
    
    # Sample records
    print("\n5. Sample Records:")
    cur.execute("""
        SELECT well_id, geology_type, aquifer_classification
        FROM wells
        WHERE geology_type IS NOT NULL
        LIMIT 5
    """)
    
    for row in cur.fetchall():
        print(f"     {row[0]:20} {row[1]:12} {row[2]:12}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✓ Database update complete!")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
