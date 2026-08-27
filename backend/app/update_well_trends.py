#!/usr/bin/env python3
"""
Update well trends in database by calculating from live model forecasts.
This ensures database cache matches actual model predictions.
"""
import sys
import os

# Add parent directory to path to import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.db import DATABASE_URL

def update_well_trends():
    """Calculate and update trend labels for all wells based on live forecasts."""
    
    # Import inference model
    model_dir = os.environ.get("MODEL_ARTIFACT_DIR", "../ml/artifacts")
    sys.path.insert(0, os.path.abspath(os.path.join(model_dir, "..")))
    from inference import ForecastModel
    
    print(f"Loading model from {model_dir}...")
    model = ForecastModel(model_dir)
    print(f"Model loaded. Graph: {model._node_feat.shape[0] if model._node_feat is not None else 0} wells")
    
    # Connect to database
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all wells with coordinates
        result = conn.execute(text("""
            SELECT well_id FROM wells 
            WHERE geom IS NOT NULL 
            ORDER BY well_id
        """))
        wells = [row[0] for row in result.fetchall()]
        
        print(f"\nProcessing {len(wells)} wells...")
        
        updated = 0
        errors = 0
        
        for i, well_id in enumerate(wells, 1):
            try:
                # Get forecast using the model via a simple forecast call
                # We'll use a simplified approach: fetch recent readings and predict
                readings_result = conn.execute(text("""
                    SELECT head_msl_m 
                    FROM readings 
                    WHERE well_id = :wid 
                    ORDER BY date DESC 
                    LIMIT 24
                """), {"wid": well_id})
                
                readings = [row[0] for row in readings_result.fetchall()]
                
                if len(readings) < 24:
                    # Not enough data - mark as Unknown
                    conn.execute(text("""
                        UPDATE wells 
                        SET trend_label = 'Unknown', forecast_decline_m = NULL 
                        WHERE well_id = :wid
                    """), {"wid": well_id})
                    conn.commit()
                    continue
                
                # Get scaler for this well
                scaler = model._scalers.get(well_id)
                if scaler is None:
                    # No scaler - mark as Unknown
                    conn.execute(text("""
                        UPDATE wells 
                        SET trend_label = 'Unknown', forecast_decline_m = NULL 
                        WHERE well_id = :wid
                    """), {"wid": well_id})
                    conn.commit()
                    continue
                
                # Scale readings
                import numpy as np
                readings.reverse()  # Oldest first
                scaled = scaler.transform(np.array(readings).reshape(-1, 1)).flatten()
                
                # Get well info
                well_info = conn.execute(text("""
                    SELECT ST_Y(geom::geometry) AS lat, ST_X(geom::geometry) AS lon,
                           aquifer_zone, geology_type, block
                    FROM wells WHERE well_id = :wid
                """), {"wid": well_id}).mappings().fetchone()
                
                zone = well_info["aquifer_zone"] or well_info["geology_type"] or "Unknown"
                
                # Predict
                if well_id in model.well_list:
                    result = model.predict_well(well_id, scaled, None, None, zone, scaler)
                else:
                    result = model.predict_point(
                        float(well_info["lat"]), float(well_info["lon"]),
                        zone, well_info["block"] or "",
                        scaled, None, None, scaler,
                        [], [], []
                    )
                
                # Calculate decline from forecast
                forecast_heads = result["forecast_head_msl"]
                decline = forecast_heads[0] - forecast_heads[-1]  # Positive = decline
                
                # Classify trend based on thresholds
                # Adjusted to match expected distribution: ~10% Critical, ~30% Watch, ~60% Stable
                if decline > 0.8:
                    trend_label = "Critical"
                elif decline > 0.2:
                    trend_label = "Watch"
                else:
                    trend_label = "Stable"
                
                # Update database
                conn.execute(text("""
                    UPDATE wells 
                    SET trend_label = :trend, forecast_decline_m = :decline 
                    WHERE well_id = :wid
                """), {"trend": trend_label, "decline": decline, "wid": well_id})
                conn.commit()
                
                updated += 1
                
                if i % 50 == 0:
                    print(f"  Processed {i}/{len(wells)} wells... (updated: {updated}, errors: {errors})")
                    
            except Exception as e:
                errors += 1
                if errors <= 5:  # Only show first 5 errors
                    print(f"  Error processing {well_id}: {e}")
                continue
        
        print(f"\n✅ Complete! Updated {updated} wells, {errors} errors")
        
        # Show distribution
        dist = conn.execute(text("""
            SELECT trend_label, COUNT(*) as count
            FROM wells
            GROUP BY trend_label
            ORDER BY count DESC
        """)).fetchall()
        
        print("\nTrend distribution:")
        for trend, count in dist:
            print(f"  {trend:12s}: {count:4d} wells")

if __name__ == "__main__":
    update_well_trends()
