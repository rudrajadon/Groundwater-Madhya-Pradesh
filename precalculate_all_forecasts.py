#!/usr/bin/env python3
"""
Pre-calculate forecasts for all wells and cache in database
This makes the API instant when users click on wells
"""

import sys
import os
import json
from datetime import datetime

# Set Render database
os.environ["DATABASE_URL"] = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

# Add ML to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import psycopg2
from psycopg2 import sql
import numpy as np

print("=" * 70)
print("PRE-CALCULATING FORECASTS FOR ALL WELLS")
print("This will make the frontend super fast!")
print("=" * 70)

# Load ML model
print("\n📦 Loading ML model...")
from inference import ForecastModel
model_dir = os.path.join(os.path.dirname(__file__), 'ml/artifacts')
model = ForecastModel(model_dir)
print(f"✅ Model loaded: {model._node_feat.shape[0]} wells in graph")

# Connect to database
print("\n🔌 Connecting to Render database...")
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Add forecast_cache column if it doesn't exist
print("📊 Setting up forecast cache table...")
try:
    cur.execute("""
        ALTER TABLE wells 
        ADD COLUMN IF NOT EXISTS forecast_cache JSONB,
        ADD COLUMN IF NOT EXISTS forecast_cached_at TIMESTAMP
    """)
    conn.commit()
    print("✅ Cache columns ready")
except Exception as e:
    print(f"⚠️  Cache columns may already exist: {e}")
    conn.rollback()

# Get all wells with sufficient data
print("\n🔍 Finding wells with enough data for forecasting...")
cur.execute("""
    SELECT w.well_id, COUNT(r.id) as reading_count,
           ST_Y(w.geom::geometry) as lat, ST_X(w.geom::geometry) as lon,
           w.aquifer_zone, w.geology_type, w.block, w.trend_label
    FROM wells w
    LEFT JOIN readings r ON w.well_id = r.well_id AND r.head_msl_m IS NOT NULL
    WHERE w.geom IS NOT NULL
    GROUP BY w.well_id, w.geom, w.aquifer_zone, w.geology_type, w.block, w.trend_label
    HAVING COUNT(r.id) >= 24
    ORDER BY w.well_id
""")

wells = cur.fetchall()
print(f"✅ Found {len(wells)} wells with sufficient data")

# Process each well
print(f"\n🚀 Processing {len(wells)} wells...")
processed = 0
cached = 0
errors = 0

for well_id, reading_count, lat, lon, aquifer_zone, geology_type, block, trend_label in wells:
    try:
        # Get last 24 readings
        cur.execute("""
            SELECT head_msl_m 
            FROM readings 
            WHERE well_id = %s AND head_msl_m IS NOT NULL
            ORDER BY date DESC 
            LIMIT 24
        """, (well_id,))
        
        readings = [row[0] for row in cur.fetchall()]
        
        if len(readings) < 24:
            continue
            
        readings.reverse()  # Oldest first
        
        # Get scaler
        scaler = model._scalers.get(well_id)
        if not scaler:
            errors += 1
            continue
        
        # Scale readings
        scaled = scaler.transform(np.array(readings).reshape(-1, 1)).flatten()
        
        # Generate forecast
        zone = aquifer_zone or geology_type or "Unknown"
        
        if well_id in model.well_list:
            result = model.predict_well(well_id, scaled, None, None, zone, scaler)
        else:
            result = model.predict_point(lat, lon, zone, block or "", scaled, k=5)
        
        # Calculate trend from forecast
        heads = result["forecast_head_msl"]
        stds = result["uncertainty_std_m"]
        
        # Calculate decline (first to last month)
        decline = heads[-1] - heads[0]
        
        # Classify trend
        if decline < -2.0:
            trend_label = "Critical"
            recommendation = f"Hydraulic head projected to drop {abs(decline):.1f}m over the next 12 months. Immediate action required."
        elif decline < -0.5:
            trend_label = "Watch"
            recommendation = f"Moderate decline projected ({abs(decline):.1f}m over 12 months). Monitor closely."
        else:
            trend_label = "Stable"
            if decline < 0:
                recommendation = f"Water levels improving (+{abs(decline):.1f}m projected). Continue current management."
            else:
                recommendation = f"Water levels stable ({decline:.2f}m change). Continue monitoring."
        
        # Create forecast cache with forecast points
        forecast_points = [
            {
                "month_index": i + 1,
                "head_msl_m": round(heads[i], 2),
                "lower_m": round(heads[i] - 1.96 * stds[i], 2),
                "upper_m": round(heads[i] + 1.96 * stds[i], 2),
            }
            for i in range(len(heads))
        ]
        
        forecast_data = {
            "well_id": well_id,
            "forecast": forecast_points,
            "trend_label": trend_label,
            "recommendation": recommendation,
            "decline_m": round(decline, 2),
            "model_version": "pgnn-lstm-v1",
            "cached_at": datetime.now().isoformat()
        }
        
        # Store in database
        cur.execute("""
            UPDATE wells 
            SET forecast_cache = %s,
                forecast_cached_at = NOW()
            WHERE well_id = %s
        """, (json.dumps(forecast_data), well_id))
        
        cached += 1
        processed += 1
        
        if processed % 50 == 0:
            conn.commit()
            print(f"  ✅ Processed {processed}/{len(wells)} wells (cached: {cached}, errors: {errors})")
            
    except Exception as e:
        errors += 1
        if processed % 50 == 0:
            print(f"  ⚠️  Error on {well_id}: {str(e)[:50]}")
        continue

conn.commit()

print(f"\n" + "=" * 70)
print(f"✅ COMPLETE!")
print(f"=" * 70)
print(f"  Processed: {processed} wells")
print(f"  Cached: {cached} forecasts")
print(f"  Errors: {errors}")
print(f"\n🎉 Your app will now be SUPER FAST!")
print(f"   Forecasts are pre-calculated and served from cache!")
print("=" * 70)

cur.close()
conn.close()
