# Trend Classification Fix - Multi-District Dataset

## Problem
After loading all GW_Data (1,307 wells from 10+ districts), most wells show "Stable" trend instead of proper distribution of Critical/Watch/Stable. This is because:

1. **Old model trained on Indore only** (52 wells)
2. **New wells from other districts** not in the model's graph structure
3. **ML predictions fail** for unknown wells → fallback to generic predictions

## Solution Implemented

### 1. Strategic Subset Selection (`etl/create_subset.py`)
Created intelligent well selection:
- **300 wells** across all districts
- Balanced distribution (33 wells per district)
- Quality criteria:
  - Minimum 24 months of data
  - Valid coordinates
  - Recent data (1990-2025)
  - Actual variation (not flat lines)
  
Result: **57,416 readings**, 108k monthly observations

### 2. Statistical Trend Fallback (`backend/app/services/statistical_trend.py`)
For wells not in the trained model:
- Uses linear regression on past 12 months
- Projects 12 months forward
- Classifies as Critical/Watch/Stable based on slope:
  - **Critical**: < -2.0 m/year decline
  - **Watch**: -0.5 to -2.0 m/year decline  
  - **Stable**: > -0.5 m/year

**Confidence scoring** based on:
- R² value (fit quality)
- Number of readings
- Data recency

### 3. Updated Forecast Endpoint
Modified `/api/v1/forecast/well/{well_id}`:
```python
# Check if well in model
well_in_model = well_id in model.well_list

if not well_in_model:
    # Use statistical trend analysis
    trend_result = compute_statistical_trend(well_id, db)
    # Generate simple linear forecast
    ...
else:
    # Use ML model
    ...
```

## Current Status

### ✅ Completed
1. Full ETL pipeline (all 21 MDB files processed)
2. 1,307 wells, 151,302 readings in database
3. Strategic subset created (300 wells)
4. Statistical trend fallback implemented
5. Backend code updated

### ⏳ In Progress
1. **Training subset model** - Running for ~15 minutes
   - 300 wells, 74k training sequences
   - Expected completion: 20-40 minutes total
   - Will provide ML predictions for all districts

2. **Backend rebuild** - Docker image rebuilding
   - New code with statistical fallback
   - Should complete in 2-3 minutes

### 📊 Expected Results (After Training Completes)

**Wells in trained subset (300)**:
- Use ML model forecasts
- GNN-based predictions with spatial relationships
- Proper trend classification based on 12-month forecast

**Wells not in subset (~1,000)**:
- Use statistical trend fallback
- Linear regression on historical data
- Still get Critical/Watch/Stable classification
- Lower confidence but reasonable estimates

## Files Modified

1. `etl/create_subset.py` - NEW: Strategic well selection
2. `backend/app/services/statistical_trend.py` - NEW: Statistical fallback
3. `backend/app/routers/forecast.py` - UPDATED: Added fallback logic
4. `infra/docker-compose.yml` - UPDATED: Added backend volume mount
5. `data/subset/` - NEW: 300-well training dataset

## Testing After Deployment

### Test Wells by District
```bash
# Indore (in original model)
curl "http://localhost:8000/api/v1/forecast/well/SIND-004-A-PZ"

# Jabalpur (new district, should use statistical)
curl "http://localhost:8000/api/v1/forecast/well/SJBP001-OW-B"

# Ujjain (new district)
curl "http://localhost:8000/api/v1/forecast/well/SUJ001-OW"
```

Expected response fields:
- `trend_label`: "Critical" | "Watch" | "Stable"
- `model_version`: "pgnn_v3_..." for ML, "statistical_v1" for fallback
- `caveat`: Explains which method was used
- `recommendation`: Actionable advice

## Performance Metrics

### Old System (Indore Only)
- Training time: ~10 minutes
- Wells covered: 52
- Readings: 13,251
- Geographic coverage: 1 district

### New System (Multi-District)
- Full dataset: 1,307 wells, 151k readings
- Training subset: 300 wells, 57k readings  
- Training time: ~30 minutes (estimated)
- Geographic coverage: 10+ districts across Madhya Pradesh

### Trend Distribution Target
- **Critical**: 10-15% of wells (major declines)
- **Watch**: 20-30% of wells (moderate declines)
- **Stable**: 55-70% of wells (stable or improving)

## Next Actions (Manual)

1. **Wait for training to complete** (~15-20 more minutes)
   ```bash
   ps aux | grep train.py  # Check if still running
   ```

2. **Check training results**
   ```bash
   tail -100 ml/training_subset.log
   ls -lh ml/artifacts/  # New model files should appear
   ```

3. **Restart backend** (after training completes)
   ```bash
   docker compose -f infra/docker-compose.yml restart backend
   ```

4. **Test frontend** - Open http://localhost:3000
   - Click on wells from different districts
   - Verify trend labels show variety (not all Stable)
   - Check recommendations are appropriate

5. **Monitor backend logs**
   ```bash
   docker logs -f infra-backend-1 | grep "statistical\|Well.*not in model"
   ```

## Troubleshooting

**If most wells still show "Stable":**
1. Check if new model loaded: `curl http://localhost:8000/health`
2. Check model metadata: `cat ml/artifacts/model_metadata.json`
3. Verify statistical fallback is working: Check logs for "not in model" messages

**If training fails:**
- Reduce epochs: `--epochs 50`
- Reduce subset size in `create_subset.py` (300 → 200)
- Check memory: Training needs ~2GB RAM

**If backend doesn't update:**
- Rebuild: `docker compose -f infra/docker-compose.yml build backend`
- Check volume mounts: `docker inspect infra-backend-1 | grep Mounts`

## Future Enhancements

1. **Incremental training**: Add new wells to existing model
2. **Ensemble predictions**: Combine ML + statistical for better accuracy  
3. **Seasonal decomposition**: Account for monsoon patterns
4. **Aquifer-specific models**: Train separate models per aquifer type
5. **Real-time updates**: Retrain monthly with new data

---

**Status**: Implementation complete, training in progress
**Date**: August 9, 2026 11:30 AM
**Next Check**: 11:45 AM (training completion expected)
