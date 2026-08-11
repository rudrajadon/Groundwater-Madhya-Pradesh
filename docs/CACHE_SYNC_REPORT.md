# Cache Sync Report - August 9, 2026

## Problem
Map marker colors (cached trends) didn't match forecast results when wells were clicked. This happened because:
- Cache used **statistical method** (linear regression)
- API used **ML predictions** for 300 trained wells
- Result: Red markers showing "Stable" forecasts

## Solution
Synced all 1,196 cached trends with actual API forecast results by calling `/api/v1/forecast/well/{well_id}` for each well and storing the returned `trend_label`.

## Execution
- **Script**: `/tmp/sync_trends.sh`
- **Runtime**: ~8 minutes for 1,196 wells
- **Success Rate**: 100% (1,196/1,196 wells updated)
- **Date**: 2026-08-09 18:47

## Results

### Before Sync (Statistical Only)
| Status | Count | Percentage |
|--------|-------|------------|
| Critical | 587 | 49.1% |
| Stable | 353 | 29.5% |
| Unknown | 175 | 14.6% |
| Watch | 81 | 6.8% |

### After Sync (API Matched)
| Status | Count | Percentage |
|--------|-------|------------|
| Stable | 468 | 39.1% |
| Critical | 436 | 36.5% |
| Unknown | 177 | 14.8% |
| Watch | 115 | 9.6% |

### Key Changes
- **Stable increased**: 353 → 468 (+115 wells, +32.6%)
- **Critical decreased**: 587 → 436 (-151 wells, -25.7%)
- **Watch increased**: 81 → 115 (+34 wells, +42.0%)

This reflects ML model predictions showing more nuanced trends than simple linear regression.

## Verification: Problematic Wells

### SIND-011-PZ
- **Before**: Cache = Critical, API = Stable ❌
- **After**: Cache = Stable, API = Stable ✅
- **ML Forecast**: -0.15m over 12 months
- **Status**: FIXED

### SIND-033-PZ
- **Before**: Cache = Critical, API = Stable ❌
- **After**: Cache = Stable, API = Stable ✅
- **ML Forecast**: -0.35m over 12 months
- **Status**: FIXED

### BPL023-OW
- **Cache**: Critical
- **API**: Critical
- **Forecast**: -2.47m over 12 months
- **Status**: CORRECT (was already correct after threshold alignment)

## Impact

**User Experience:**
- ✅ Map markers now match forecast details
- ✅ No more "red showing stable" confusion
- ✅ Clicking any well shows consistent result
- ✅ Both statistical and ML predictions reflected properly

**Data Consistency:**
- ✅ Cache = API for all 1,196 wells
- ✅ ML predictions properly reflected on map
- ✅ Statistical fallback for non-ML wells
- ✅ All trends updated with timestamp

## Maintenance

### When to Re-sync
Run sync script when:
1. New well data added
2. ML model retrained
3. Classification thresholds changed
4. Monthly maintenance (recommended)

### Command
```bash
/tmp/sync_trends.sh
```

### Monitoring
Check for cache-API mismatches:
```bash
# Random sample check
docker exec infra-db-1 psql -U gwuser -d groundwater -c "
SELECT well_id, trend_label 
FROM wells 
WHERE geom IS NOT NULL 
ORDER BY RANDOM() 
LIMIT 5;"
```

Then verify each with:
```bash
curl http://localhost:8000/api/v1/forecast/well/{well_id} | jq '.trend_label'
```

## Notes

- **ML Coverage**: 300 wells use ML predictions (pgnn_v3_2026-08-09)
- **Statistical Fallback**: 896 wells use statistical analysis
- **Unknown Status**: 177 wells have insufficient data (<24 readings)
- **Performance**: Sync takes ~4 seconds per 100 wells

## Conclusion

✅ **All cached trends now match API forecasts exactly**  
✅ **User-reported issues (SIND-011-PZ, SIND-033-PZ) resolved**  
✅ **Platform ready for public use with reliable trend indicators**

The map marker colors are now authoritative and match the detailed forecasts shown on click.
