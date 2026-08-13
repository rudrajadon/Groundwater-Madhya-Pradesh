#!/usr/bin/env python3
"""
Re-predict trends for all wells using the trained PGNN-LSTM model.
Updates the wells table with ML-predicted trend labels and 12-month forecasts.
"""
import os
import sys
import pickle
import json
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
import torch

# Add ml directory to path to import inference module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))
from inference import ForecastModel

SEQ_LEN = 24

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'groundwater',
    'user': 'gwuser',
    'password': 'changeme'
}


def classify_trend(forecast_values):
    """
    Classify trend based on 12-month forecast values.
    
    ORIGINAL THRESHOLDS (restored):
    Critical: > 4m decline over 12 months
    Watch: 2-4m decline
    Stable: 0-2m decline or any improvement
    Unknown: Insufficient/unreliable data
    
    Returns: 'Critical', 'Watch', 'Stable', or 'Unknown'
    """
    if not forecast_values or len(forecast_values) < 2:
        return 'Unknown'
    
    # Check if forecast is likely statistical (straight line pattern)
    # Statistical forecasts have nearly constant differences between consecutive values
    if len(forecast_values) >= 6:
        diffs = [forecast_values[i+1] - forecast_values[i] for i in range(len(forecast_values)-1)]
        avg_diff = sum(diffs) / len(diffs)
        diff_variance = sum((d - avg_diff)**2 for d in diffs) / len(diffs)
        
        # If variance is very low, it's likely a straight line (statistical)
        # Mark as Unknown since it's not a real ML prediction
        if diff_variance < 0.01:  # Very low variance = straight line
            return 'Unknown'
    
    # Calculate total change from first to last month (negative = decline)
    total_change = forecast_values[-1] - forecast_values[0]
    
    # Apply user-specified thresholds
    # Stable: 0-2m decline
    # Watch: 2-4m decline  
    # Critical: >4m decline
    if total_change < -4.0:
        return 'Critical'
    elif total_change < -2.0:
        return 'Watch'
    else:
        # 0-2m decline or any improvement = Stable
        return 'Stable'


def get_well_recent_data(conn, well_id, seq_len=SEQ_LEN):
    """
    Fetch the most recent seq_len readings for a well.
    Returns: (scaled_series, scaler, raw_values) or (None, None, None)
    """
    cur = conn.cursor()
    
    # Get recent readings
    cur.execute("""
        SELECT head_msl_m 
        FROM readings 
        WHERE well_id = %s AND head_msl_m IS NOT NULL
        ORDER BY date DESC 
        LIMIT %s
    """, (well_id, seq_len))
    
    rows = cur.fetchall()
    cur.close()
    
    if len(rows) < seq_len:
        return None, None, None
    
    # Reverse to get chronological order
    values = np.array([r[0] for r in reversed(rows)])
    
    # Create MinMaxScaler equivalent
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(values.reshape(-1, 1)).flatten()
    
    return scaled, scaler, values


def main():
    print("=" * 80)
    print("UPDATING WELL TRENDS FROM TRAINED ML MODEL")
    print("=" * 80)
    
    # Load the trained model
    artifact_dir = 'ml/artifacts'
    if not os.path.exists(artifact_dir):
        print(f"Error: Artifact directory not found: {artifact_dir}")
        return 1
    
    print(f"\n1. Loading trained PGNN-LSTM model from {artifact_dir}...")
    model = ForecastModel(artifact_dir)
    print(f"   ✓ Model loaded with {len(model.well_list)} trained wells")
    
    # Connect to database
    print(f"\n2. Connecting to PostgreSQL database...")
    conn = psycopg2.connect(**DB_CONFIG)
    print(f"   ✓ Connected to {DB_CONFIG['database']}")
    
    # Get all wells with their metadata
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            well_id, 
            ST_Y(geom::geometry) as lat,
            ST_X(geom::geometry) as lon,
            aquifer_zone, 
            block, 
            district
        FROM wells
        WHERE geom IS NOT NULL
        ORDER BY well_id
    """)
    wells = cur.fetchall()
    cur.close()
    
    print(f"\n3. Found {len(wells)} wells in database")
    print(f"   Will predict trends for wells with sufficient data...")
    
    # Track results
    predictions = []
    errors = []
    
    print(f"\n4. Running predictions...")
    for idx, (well_id, lat, lon, aquifer_zone, block, district) in enumerate(wells, 1):
        if idx % 50 == 0 or idx == 1:
            print(f"   Processing well {idx}/{len(wells)}: {well_id}")
        
        try:
            # Check if well is in trained model
            if well_id not in model.well_list:
                errors.append((well_id, "Not in trained model"))
                continue
            
            # Get recent data
            scaled_series, scaler, raw_values = get_well_recent_data(conn, well_id, SEQ_LEN)
            if scaled_series is None:
                errors.append((well_id, f"Insufficient data (need {SEQ_LEN} readings)"))
                continue
            
            # Make prediction
            result = model.predict_well(
                well_id=well_id,
                recent_scaled_series=scaled_series,
                node_feat=None,  # Not used, model has cached graph
                adj=None,        # Not used, model has cached graph
                aquifer_zone=aquifer_zone or 'Unknown',
                scaler=scaler
            )
            
            # Extract forecast and classify trend
            forecast = result['forecast_head_msl']
            uncertainty = result['uncertainty_std_m']
            trend_label = classify_trend(forecast)
            
            predictions.append({
                'well_id': well_id,
                'trend_label': trend_label,
                'forecast': forecast,
                'uncertainty': uncertainty,
                'current_level': float(raw_values[-1])
            })
            
        except Exception as e:
            errors.append((well_id, str(e)))
    
    print(f"\n5. Prediction Results:")
    print(f"   ✓ Successful predictions: {len(predictions)}")
    print(f"   ✗ Failed/skipped: {len(errors)}")
    
    if predictions:
        # Show trend distribution
        trend_counts = {}
        for p in predictions:
            trend = p['trend_label']
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
        
        print(f"\n6. Trend Distribution:")
        total = len(predictions)
        for trend in ['Critical', 'Watch', 'Stable', 'Unknown']:
            count = trend_counts.get(trend, 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"   {trend:12s}: {count:4d} wells ({pct:5.1f}%)")
        
        # Update database
        print(f"\n7. Updating database with predictions...")
        cur = conn.cursor()
        
        # Update trend_label for all predicted wells
        update_data = [(p['trend_label'], p['well_id']) for p in predictions]
        execute_values(
            cur,
            "UPDATE wells SET trend_label = data.label FROM (VALUES %s) AS data(label, id) WHERE well_id = data.id",
            update_data
        )
        
        conn.commit()
        cur.close()
        print(f"   ✓ Updated {len(predictions)} wells in database")
        
        # Save detailed predictions to JSON
        output_file = 'well_predictions_detailed.json'
        with open(output_file, 'w') as f:
            json.dump(predictions, f, indent=2)
        print(f"   ✓ Saved detailed predictions to {output_file}")
    
    if errors:
        print(f"\n8. Errors/Warnings ({len(errors)} wells):")
        # Group errors by type
        error_types = {}
        for well_id, error in errors:
            error_types.setdefault(error, []).append(well_id)
        
        for error, well_ids in error_types.items():
            print(f"   • {error}: {len(well_ids)} wells")
            if len(well_ids) <= 5:
                print(f"     Wells: {', '.join(well_ids)}")
    
    conn.close()
    print(f"\n{'=' * 80}")
    print("DONE! All trends updated from ML model predictions.")
    print(f"{'=' * 80}\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
