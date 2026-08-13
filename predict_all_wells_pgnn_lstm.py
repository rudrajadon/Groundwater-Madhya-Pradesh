#!/usr/bin/env python3
"""
Use the trained PGNN-LSTM model (pgnn_lstm_best.pt) to predict trends for ALL wells.
Uses the existing inference.py infrastructure.
Applies thresholds: 0-2m stable, 2-4m watch, >4m critical
"""
import sys
import os
import json
import psycopg2
import numpy as np

# Add ml directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))

from ml.inference import ForecastModel

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'groundwater',
    'user': 'gwuser',
    'password': 'changeme'
}

# Thresholds (user-specified)
CRITICAL_THRESHOLD = -4.0  # >4m decline over 12 months
WATCH_THRESHOLD = -2.0     # 2-4m decline over 12 months

def classify_trend(forecast):
    """Classify trend based on 12-month forecast change."""
    change = forecast[-1] - forecast[0]
    
    if change <= CRITICAL_THRESHOLD:
        return 'Critical'
    elif change <= WATCH_THRESHOLD:
        return 'Watch'
    else:
        return 'Stable'

def get_well_data(well_id, conn):
    """Fetch recent water level readings for a well."""
    cur = conn.cursor()
    cur.execute("""
        SELECT date, head_msl_m
        FROM readings
        WHERE well_id = %s
          AND head_msl_m IS NOT NULL
        ORDER BY date DESC
        LIMIT 24
    """, (well_id,))
    
    rows = cur.fetchall()
    cur.close()
    
    if len(rows) < 24:
        return None
    
    # Reverse to get chronological order
    rows = rows[::-1]
    dates = [r[0] for r in rows]
    values = [float(r[1]) for r in rows]
    
    return dates, values

def get_well_metadata(well_id, conn):
    """Fetch well metadata (geology, block)."""
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            aquifer_classification,
            block,
            lat_raw as lat,
            lon_raw as lon
        FROM wells
        WHERE well_id = %s
    """, (well_id,))
    
    row = cur.fetchone()
    cur.close()
    
    if row:
        return {
            'geology': row[0] or 'Unknown',
            'block': row[1] or 'Unknown',
            'lat': float(row[2]) if row[2] else None,
            'lon': float(row[3]) if row[3] else None
        }
    return None

def main():
    print("="*80)
    print("PGNN-LSTM PREDICTION FOR ALL WELLS")
    print("="*80)
    print("\nLoading model...")
    
    # Load model
    model = ForecastModel(artifact_dir='ml/artifacts')
    
    print(f"\n✓ Model loaded successfully")
    print(f"  Trained wells: {len(model.well_list)}")
    print(f"  Graph nodes: {model._node_feat.shape[0]}")
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get all wells
    cur.execute("SELECT well_id FROM wells ORDER BY well_id")
    all_wells = [r[0] for r in cur.fetchall()]
    
    print(f"\nProcessing {len(all_wells)} wells...")
    
    results = []
    success = 0
    no_data = 0
    no_model = 0
    errors = 0
    
    for i, well_id in enumerate(all_wells):
        if (i + 1) % 100 == 0:
            print(f"  Processed {i+1}/{len(all_wells)} wells...")
        
        try:
            # Check if well is in model
            if well_id not in model._well_to_idx:
                no_model += 1
                continue
            
            # Get well data
            data = get_well_data(well_id, conn)
            if data is None:
                no_data += 1
                continue
            
            dates, values = data
            
            # Get metadata
            metadata = get_well_metadata(well_id, conn)
            if metadata is None or metadata['geology'] == 'Unknown':
                no_data += 1
                continue
            
            # Get scaler
            if well_id not in model._scalers:
                no_model += 1
                continue
            
            scaler = model._scalers[well_id]
            
            # Normalize input
            scaled_values = scaler.transform(np.array(values).reshape(-1, 1)).flatten()
            
            # Get node features
            well_idx = model._well_to_idx[well_id]
            node_feat = model._node_feat
            adj = model._adj
            
            # Make prediction
            import torch
            wl_tensor = torch.FloatTensor(scaled_values).unsqueeze(0).unsqueeze(-1)
            wi_tensor = torch.LongTensor([well_idx])
            geo_list = [metadata['geology']]
            
            with torch.no_grad():
                forecast_scaled = model._model.forward_with_embed(
                    wl_tensor,
                    model._g_embed,
                    wi_tensor,
                    geo_list
                ).squeeze().numpy()
            
            # Denormalize
            forecast = scaler.inverse_transform(forecast_scaled.reshape(-1, 1)).flatten()
            
            # Classify trend
            trend_label = classify_trend(forecast)
            change_12m = forecast[-1] - forecast[0]
            
            # Update database
            cur.execute("""
                UPDATE wells
                SET trend_label = %s
                WHERE well_id = %s
            """, (trend_label, well_id))
            
            results.append({
                'well_id': well_id,
                'trend_label': trend_label,
                'change_12m': float(change_12m),
                'forecast': forecast.tolist(),
                'last_reading': float(values[-1])
            })
            
            success += 1
            
        except Exception as e:
            print(f"  Error processing {well_id}: {e}")
            errors += 1
            continue
    
    conn.commit()
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}\n")
    print(f"Success: {success} wells")
    print(f"No data (insufficient readings): {no_data} wells")
    print(f"Not in model: {no_model} wells")
    print(f"Errors: {errors} wells")
    
    # Distribution
    if len(results) > 0:
        critical = [r for r in results if r['trend_label'] == 'Critical']
        watch = [r for r in results if r['trend_label'] == 'Watch']
        stable = [r for r in results if r['trend_label'] == 'Stable']
        
        print(f"\nTrend Distribution (Thresholds: 0-2m stable, 2-4m watch, >4m critical):")
        print(f"  Critical (>4m decline): {len(critical)} ({100*len(critical)/len(results):.1f}%)")
        print(f"  Watch (2-4m decline): {len(watch)} ({100*len(watch)/len(results):.1f}%)")
        print(f"  Stable (0-2m): {len(stable)} ({100*len(stable)/len(results):.1f}%)")
    else:
        print("\nNo results - all wells failed")
        return
    
    # Show critical wells
    if critical:
        print(f"\nCritical Wells:")
        critical.sort(key=lambda x: x['change_12m'])
        for r in critical[:15]:
            print(f"  {r['well_id']:<20} {r['change_12m']:>6.2f}m decline")
        if len(critical) > 15:
            print(f"  ... and {len(critical)-15} more")
    
    # Show watch wells
    if watch:
        print(f"\nWatch Wells (showing first 15):")
        watch.sort(key=lambda x: x['change_12m'])
        for r in watch[:15]:
            print(f"  {r['well_id']:<20} {r['change_12m']:>6.2f}m decline")
        if len(watch) > 15:
            print(f"  ... and {len(watch)-15} more")
    
    # Save results
    with open('pgnn_lstm_predictions.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Saved predictions to pgnn_lstm_predictions.json")
    
    conn.close()
    
    print(f"\n{'='*80}")
    print("✓ DONE! Using trained PGNN-LSTM model")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
