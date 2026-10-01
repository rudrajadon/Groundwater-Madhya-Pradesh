#!/usr/bin/env python3
"""
Copy the trend labels that were calculated locally by your ML model
This uses the backend's update_well_trends.py logic but runs against Render
"""

import sys
import os

# Set the database URL to Render
os.environ["DATABASE_URL"] = "postgresql://groundwater_user:bLSvm2uNjYruEANioWxLyqZqvBp8orHz@dpg-dac2r9nqj5pc739q2cq0-a.oregon-postgres.render.com/groundwater_9a4l"

# Add ML directory to path
ml_path = os.path.join(os.path.dirname(__file__), 'ml')
sys.path.insert(0, ml_path)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("RUNNING ML MODEL TREND CALCULATION ON RENDER DATABASE")
print("=" * 60)

# Set model artifact directory
os.environ["MODEL_ARTIFACT_DIR"] = os.path.join(os.path.dirname(__file__), 'ml/artifacts')

# Import and run the actual backend trend update script
from app.update_well_trends import update_well_trends

try:
    update_well_trends()
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Trends updated using ML model predictions!")
    print("=" * 60)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\nThis requires the ML model artifacts to be present.")
    print("Make sure ml/artifacts directory has the trained model files.")
