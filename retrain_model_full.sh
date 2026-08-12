#!/bin/bash
set -e

echo "=========================================="
echo "FULL ML MODEL RETRAINING"
echo "=========================================="
echo ""

cd /Users/rudrajadon/Downloads/groundwater-app

# Activate virtual environment
source .venv/bin/activate

echo "Step 1: Export fresh data from database..."
python3 etl/export_to_csv.py

echo ""
echo "Step 2: Fetch rainfall data (if not already done)..."
# python3 etl/fetch_rainfall_openmeteo.py  # Skip if already done

echo ""
echo "Step 3: Prepare training data..."
python3 ml/prepare_training_data.py

echo ""
echo "Step 4: Train PGNN-LSTM model..."
python3 ml/train.py

echo ""
echo "Step 5: Update database with ML predictions..."
python3 update_trends_from_model.py

echo ""
echo "=========================================="
echo "✓ RETRAINING COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart backend: cd infra && docker-compose restart backend"
echo "2. Hard refresh frontend: Cmd+Shift+R"
