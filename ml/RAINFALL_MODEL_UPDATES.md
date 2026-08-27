# ML Model Updates for Rainfall Integration

## Changes Made

### 1. Model Architecture (`ml/model.py`)

**Updated `PGNN_LSTM` class:**
- ✅ Node features: 8 → 9 (added rainfall statistics)
- ✅ Sequence input: [B, 24, 1] → [B, 24, 2] (water level + rainfall)
- ✅ LSTM input dimension: `1 + gcn_h` → `2 + gcn_h`
- ✅ Added `use_rainfall` parameter for backward compatibility

### 2. Preprocessing Updates Needed

**File: `ml/preprocessing.py`**

```python
def load_rainfall_for_sequences(wells, rainfall_df, start_date, end_date):
    """Load and align rainfall data with water level sequences."""
    # Extract rainfall for date range
    # Interpolate missing values
    # Return normalized rainfall sequences
    pass

def build_sequences_with_rainfall(wl, rainfall, seq_len=24, horizon=12):
    """Create paired (water_level, rainfall) sequences."""
    # Align timestamps
    # Create sliding windows
    # Return [N, 24, 2] arrays
    pass
```

### 3. Training Data Preparation

**New script needed: `ml/prepare_training_data_v2.py`**

```python
# Load water levels
# Load rainfall from data/rainfall_well_monthly.csv
# Merge on (well_id, year, month)
# Create sequences with both channels
# Save to artifacts/sequences_v2.pkl
```

### 4. Retraining Strategy

**Command:**
```bash
cd ml
python prepare_training_data_v2.py  # Create new sequences
python train.py  # Train with rainfall features
```

**Expected Results:**
- R² improvement: 0.65 → 0.70-0.75
- RMSE reduction: 3.40m → 2.8-3.0m
- Better monsoon predictions

### 5. Model Versioning

- **Baseline**: `pgnn_lstm_best.pt` (no rainfall)
- **V2**: `pgnn_lstm_rainfall_best.pt` (with rainfall)
- Metadata tracks model version

## Implementation Status

- ✅ Model architecture updated (backward compatible)
- ⏳ Preprocessing functions (documented, needs implementation)
- ⏳ Training data preparation (documented)  
- ⏳ Actual retraining (can be done when ready)

## Next Steps

1. Implement preprocessing functions
2. Prepare training data with rainfall
3. Retrain model
4. Compare baseline vs rainfall model
5. Deploy best performer

---

**Note**: Model is ready for rainfall input. Actual retraining requires:
- Time: ~90 minutes
- Data: Aligned water level + rainfall sequences
- Compute: CPU (current setup) or GPU (faster)

**Status**: Architecture ready, awaiting data preparation & retraining session.
