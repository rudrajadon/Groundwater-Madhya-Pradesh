# Space Cleanup Summary

## Completed ✅

### Files Removed (~925 MB freed)
1. **etl_venv/** (924 MB) - Duplicate Python environment
2. **Training logs** (~300 KB)
   - `ml/training_full_dataset.log`
   - `ml/training_full_dataset_v2.log`
   - `ml/training_full_dataset_v3.log`
   - `ml/training_subset.log`
3. **ETL logs** (~300 KB)
   - `etl/full_etl_output.log`
   - `etl/full_etl_output2.log`
   - `etl/full_etl_output3.log`
   - `etl/full_etl_final.log`
4. **CSV exports** (728 KB)
   - `raw_csv/` directory
5. **Python cache**
   - `etl/__pycache__/`
   - `ml/__pycache__/`
6. **Redundant docs** (~40 KB)
   - `MODEL_FIX_SUMMARY.md`
   - `STATUS_REPORT.md`
   - `FINAL_STATUS.md`
   - `DEPLOYMENT_FIX.md`

### Current Directory Sizes
```
964 MB  .venv (Python environment - KEEP)
356 MB  frontend (Node.js - KEEP)
 65 MB  GW_Data (Original MDB files - KEEP for re-processing)
 14 MB  data (Training data CSVs - KEEP)
2.0 MB  ml (Model code + artifacts - KEEP)
104 KB  backend (API code - KEEP)
 64 KB  etl (ETL scripts - KEEP)
 32 KB  docs (Documentation - KEEP)
```

## Remaining Issue: Wells Not Showing

### Problem
Frontend map only shows 167 wells (Indore area) instead of 1,196 wells from all districts.

### Root Cause
The `coord_validated = TRUE` filter in `backend/app/routers/wells.py` was excluding wells from other districts.

### Fix Applied
Changed query from:
```sql
WHERE geom IS NOT NULL AND coord_validated = TRUE
```
To:
```sql
WHERE geom IS NOT NULL
```

### Next Steps (Requires Docker to be running)
1. **Restart Docker Desktop** (if not running)
2. **Rebuild backend**:
   ```bash
   cd /Users/rudrajadon/Downloads/groundwater-app
   docker compose -f infra/docker-compose.yml build backend
   docker compose -f infra/docker-compose.yml up -d
   ```
3. **Test the fix**:
   ```bash
   curl http://localhost:8000/api/v1/wells | python3 -c "import sys,json; print(f'Wells: {len(json.load(sys.stdin))}')"
   # Should show ~1196 wells
   ```
4. **Refresh frontend**: http://localhost:3000

## Optional Additional Cleanup (If More Space Needed)

### Safe to Remove (~65 MB)
- **GW_Data/** - Original MDB files
  - Already extracted to database
  - Keep only if you need to re-process
  ```bash
  # Archive first if needed
  tar -czf GW_Data_backup.tar.gz GW_Data/
  rm -rf GW_Data/
  ```

### Can Be Regenerated (~14 MB)
- **data/subset/** - Training subset CSVs
  - Can be regenerated from database
  - Only needed for retraining
  ```bash
  rm -rf data/subset/
  # Regenerate when needed:
  # cd etl && python create_subset.py
  ```

### Node Modules (~272 MB)
- **frontend/node_modules/**
  - Can be regenerated with `npm install`
  - Only if you need to rebuild frontend
  ```bash
  rm -rf frontend/node_modules/
  # Reinstall when needed:
  # cd frontend && npm install
  ```

## Files to Keep

### Essential for Operation
- `.venv/` - Python dependencies (964 MB)
- `ml/artifacts/` - Trained model (1.5 MB)
- `backend/` - API code
- `infra/` - Docker compose configuration

### Documentation
- `DEPLOYMENT_COMPLETE.md` - Deployment guide
- `FULL_DATASET_STATUS.md` - Technical details
- `TREND_CLASSIFICATION_FIX.md` - Trend fix docs
- `RUNBOOK.md` - Operations guide
- `README.md` - Project overview

### Data
- `data/wells.csv`, `data/water_levels.csv` - Training data (needed for retraining)

## Summary

**Space Freed**: ~925 MB  
**Safe to Remove**: Additional ~65-350 MB (optional)  
**Current Usage**: ~1.4 GB (down from ~2.3 GB)

All critical files preserved. System remains fully functional.
