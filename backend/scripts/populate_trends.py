#!/usr/bin/env python3
"""
Populate trend_label for all wells in the database.

This script fetches forecasts for all wells and caches the trend labels
in the database for faster map loading.
"""
import os
import sys
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://gwuser:gwpassword@localhost:5432/groundwater')
engine = create_engine(DATABASE_URL)


def populate_trends():
    """Populate trend labels for all wells with coordinates."""
    
    with Session(engine) as db:
        # Get all wells with coordinates
        result = db.execute(text("""
            SELECT well_id FROM wells 
            WHERE geom IS NOT NULL 
            ORDER BY well_id
        """))
        wells = [row[0] for row in result]
        
        print(f"Found {len(wells)} wells with coordinates")
        print("Computing trends...")
        
        success = 0
        no_data = 0
        errors = 0
        
        for i, well_id in enumerate(wells):
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(wells)} ({100*(i+1)/len(wells):.1f}%)")
            
            try:
                # Import here to use the same logic as the API
                from app.services.statistical_trend import compute_statistical_trend
                
                # Check if well has any readings
                reading_count = db.execute(text("""
                    SELECT COUNT(*) as cnt FROM readings 
                    WHERE well_id = :wid AND head_msl_m IS NOT NULL
                """), {"wid": well_id}).scalar()
                
                if reading_count == 0:
                    # No data - mark as Unknown
                    db.execute(text("""
                        UPDATE wells 
                        SET trend_label = 'Unknown',
                            trend_updated_at = :now
                        WHERE well_id = :wid
                    """), {"wid": well_id, "now": datetime.now()})
                    no_data += 1
                else:
                    # Compute trend
                    trend_result = compute_statistical_trend(well_id, db, months_lookback=12)
                    trend_label = trend_result.get('trend_label', 'Stable')
                    
                    # Update database
                    db.execute(text("""
                        UPDATE wells 
                        SET trend_label = :label,
                            trend_updated_at = :now
                        WHERE well_id = :wid
                    """), {"wid": well_id, "label": trend_label, "now": datetime.now()})
                    success += 1
                
                # Commit every 50 wells
                if (i + 1) % 50 == 0:
                    db.commit()
                    
            except Exception as e:
                print(f"  Error processing {well_id}: {e}")
                errors += 1
                continue
        
        # Final commit
        db.commit()
        
        print(f"\n✓ Complete!")
        print(f"  Success: {success} wells with trends")
        print(f"  No data: {no_data} wells marked as Unknown")
        print(f"  Errors: {errors} wells")
        
        # Show distribution
        print(f"\nTrend distribution:")
        result = db.execute(text("""
            SELECT trend_label, COUNT(*) as count
            FROM wells
            WHERE geom IS NOT NULL AND trend_label IS NOT NULL
            GROUP BY trend_label
            ORDER BY count DESC
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]} wells")


if __name__ == '__main__':
    print("=" * 60)
    print("TREND POPULATION SCRIPT")
    print("=" * 60)
    start_time = time.time()
    
    populate_trends()
    
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f} seconds")
