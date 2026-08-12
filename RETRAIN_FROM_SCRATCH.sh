#!/bin/bash
set -e

echo "=========================================================================="
echo "COMPLETE ML MODEL RETRAINING FROM SCRATCH"
echo "=========================================================================="
echo ""
echo "This will:"
echo "1. Export fresh data from PostgreSQL database"
echo "2. Prepare training sequences with proper preprocessing"  
echo "3. Train PGNN-LSTM model from scratch"
echo "4. Update all well predictions in database"
echo ""
read -p "This will take 30-60 minutes. Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

cd /Users/rudrajadon/Downloads/groundwater-app

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Step 1: Export fresh data from database
echo ""
echo "=========================================================================="
echo "STEP 1: Exporting fresh data from database..."
echo "=========================================================================="
export DATABASE_URL=postgresql://gwuser:changeme@localhost:5432/groundwater
python3 etl/export_to_csv.py

# Copy to ml/data for training
echo ""
echo "Copying data to ml/data directory..."
mkdir -p ml/data
cp data/water_levels.csv ml/data/
cp data/wells.csv ml/data/
cp data/litho.csv ml/data/

# Check data
echo ""
echo "Data summary:"
wc -l ml/data/*.csv

# Step 2: Run preprocessing to create sequences and graph
echo ""
echo "=========================================================================="
echo "STEP 2: Running preprocessing (creating sequences and graph)..."
echo "=========================================================================="

# Create a preprocessing script that uses the actual training pipeline
cat > ml/run_preprocessing.py << 'PREP_EOF'
#!/usr/bin/env python3
"""
Preprocessing for PGNN-LSTM using the exact same logic as original training.
Creates sequences.pkl and graph_cache.pkl in ml/artifacts/
"""
import os
import sys
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# Add ml directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from preprocessing import prepare_all

def main():
    print("="*70)
    print("PGNN-LSTM Data Preprocessing")
    print("="*70)
    
    # Load data
    print("\nLoading data...")
    wells = pd.read_csv('ml/data/wells.csv')
    litho = pd.read_csv('ml/data/litho.csv')
    wl = pd.read_csv('ml/data/water_levels.csv')
    
    print(f"  Wells: {len(wells)}")
    print(f"  Water level records: {len(wl)}")
    print(f"  Lithology records: {len(litho)}")
    
    # Run preprocessing (from preprocessing.py)
    print("\nRunning preprocessing pipeline...")
    data = prepare_all(wells, litho, wl)
    
    print(f"\nPreprocessed data:")
    print(f"  Wells with sufficient data: {len(data.well_list)}")
    print(f"  Graph nodes: {data.adj.shape[0]}")
    print(f"  Graph edges: {int((data.adj > 0).sum())}")
    
    # Create sequences
    print("\nCreating training/test sequences...")
    SEQ_LEN = 24
    HORIZON = 12
    
    train_X, train_y, train_wi, train_geo = [], [], [], []
    test_X, test_y, test_wi, test_geo = [], [], [], []
    scalers = {}
    
    for well_id in data.well_list:
        if well_id not in data.monthly:
            continue
        
        series = data.monthly[well_id].values
        if len(series) < SEQ_LEN + HORIZON:
            continue
        
        # Create scaler for this well
        scaler = MinMaxScaler(feature_range=(0, 1))
        series_scaled = scaler.fit_transform(series.reshape(-1, 1)).flatten()
        scalers[well_id] = scaler
        
        well_idx = data.well_list.index(well_id)
        geology = data.aq_info.get(well_id, {}).get('dominant', 'Unknown')
        
        # Create sequences
        for i in range(len(series_scaled) - SEQ_LEN - HORIZON + 1):
            X = series_scaled[i:i+SEQ_LEN]
            y = series_scaled[i+SEQ_LEN:i+SEQ_LEN+HORIZON]
            
            # Split train/test by date (80/20)
            if i < int(0.8 * (len(series_scaled) - SEQ_LEN - HORIZON + 1)):
                train_X.append(X)
                train_y.append(y)
                train_wi.append(well_idx)
                train_geo.append(geology)
            else:
                test_X.append(X)
                test_y.append(y)
                test_wi.append(well_idx)
                test_geo.append(geology)
    
    print(f"\n  Training sequences: {len(train_X):,}")
    print(f"  Test sequences: {len(test_X):,}")
    print(f"  Wells with scalers: {len(scalers)}")
    
    # Convert to tensors
    import torch
    sequences = {
        'train_X': torch.FloatTensor(np.array(train_X)).unsqueeze(-1),
        'train_y': torch.FloatTensor(np.array(train_y)),
        'train_wi': torch.LongTensor(train_wi),
        'train_geo': train_geo,
        'test_X': torch.FloatTensor(np.array(test_X)).unsqueeze(-1),
        'test_y': torch.FloatTensor(np.array(test_y)),
        'test_wi': torch.LongTensor(test_wi),
        'test_geo': test_geo,
    }
    
    graph_cache = {
        'adj': torch.FloatTensor(data.adj),
        'node_feat': torch.FloatTensor(data.node_feats),
        'well_to_idx': {w: i for i, w in enumerate(data.well_list)},
    }
    
    # Save
    os.makedirs('ml/artifacts', exist_ok=True)
    
    with open('ml/artifacts/sequences.pkl', 'wb') as f:
        pickle.dump(sequences, f)
    print(f"\n✓ Saved sequences to ml/artifacts/sequences.pkl")
    
    with open('ml/artifacts/graph_cache.pkl', 'wb') as f:
        pickle.dump(graph_cache, f)
    print(f"✓ Saved graph cache to ml/artifacts/graph_cache.pkl")
    
    with open('ml/artifacts/scalers.pkl', 'wb') as f:
        pickle.dump(scalers, f)
    print(f"✓ Saved scalers to ml/artifacts/scalers.pkl")
    
    print("\n" + "="*70)
    print("✓ Preprocessing complete!")
    print("="*70)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
PREP_EOF

chmod +x ml/run_preprocessing.py
python3 ml/run_preprocessing.py

# Step 3: Train the model
echo ""
echo "=========================================================================="
echo "STEP 3: Training PGNN-LSTM model..."
echo "=========================================================================="
python3 ml/train.py

# Step 4: Update database with predictions
echo ""
echo "=========================================================================="
echo "STEP 4: Updating database with ML predictions..."
echo "=========================================================================="
python3 update_trends_from_model.py

# Step 5: Restart backend
echo ""
echo "=========================================================================="
echo "STEP 5: Restarting backend to load new model..."
echo "=========================================================================="
cd infra
docker-compose restart backend
sleep 3
cd ..

# Final verification
echo ""
echo "=========================================================================="
echo "VERIFICATION"
echo "=========================================================================="
echo ""
echo "Database trends:"
docker exec infra-db-1 psql -U gwuser -d groundwater -c "
SELECT trend_label, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM wells WHERE trend_label IS NOT NULL), 1) as pct
FROM wells 
WHERE trend_label IS NOT NULL
GROUP BY trend_label
ORDER BY CASE trend_label WHEN 'Critical' THEN 1 WHEN 'Watch' THEN 2 WHEN 'Stable' THEN 3 ELSE 4 END;
"

echo ""
echo "Backend status:"
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "=========================================================================="
echo "✓ COMPLETE! Model retrained from scratch with fresh database data."
echo "=========================================================================="
echo ""
echo "Next steps:"
echo "1. Hard refresh frontend: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)"
echo "2. Test a well: curl http://localhost:8000/api/v1/forecast/well/BPL001-OW"
echo "3. Check the map for updated trend colors"
echo ""
