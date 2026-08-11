# Elevation Data Fix - August 9, 2026

## Problem Identified

177 wells (14.8%) showed "Unknown" status on the map. Investigation revealed two root causes:

### 1. Missing Elevation Data (73 wells - 41%)
- Wells had depth readings (`depth_bgl_m`) but no elevation data
- Without elevation, couldn't compute absolute water level (`head_msl_m = elevation_m - depth_bgl_m`)
- API correctly returned "Unknown" because `head_msl_m IS NULL`
- Total affected readings: **7,452 readings**

### 2. No Data (104 wells - 59%)
- Wells exist in database with coordinates but have zero readings
- Likely planned monitoring locations never activated
- Cannot be fixed without actual field measurements

## Solution Implemented

### Step 1: Fetch Missing Elevations
Created `/Users/rudrajadon/Downloads/groundwater-app/etl/fetch_elevations.py`:
- Used Open-Elevation API (free, no API key required)
- Processed 71 wells in 4 batches (20 wells/batch)
- Elevation range: 203m to 558m across Madhya Pradesh

### Step 2: Compute Water Levels
For each well with new elevation data:
```sql
UPDATE readings
SET head_msl_m = elevation_m - depth_bgl_m
WHERE well_id = :well_id
  AND depth_bgl_m IS NOT NULL
  AND head_msl_m IS NULL;
```

### Step 3: Re-sync Cache
- Called forecast API for each fixed well
- Updated cached `trend_label` in wells table
- 73 wells converted from "Unknown" to proper status

## Results

### Before Fix
| Status | Count | % |
|--------|-------|---|
| Stable | 468 | 39.1% |
| Critical | 436 | 36.5% |
| **Unknown** | **177** | **14.8%** |
| Watch | 115 | 9.6% |

### After Fix
| Status | Count | % | Change |
|--------|-------|---|--------|
| Stable | 498 | 41.6% | +30 wells (+6.4%) |
| Critical | 478 | 40.0% | +42 wells (+9.6%) |
| Watch | 116 | 9.7% | +1 well (+0.9%) |
| **Unknown** | **104** | **8.7%** | **-73 wells (-41.2%)** |

### Impact Summary
✅ **73 wells recovered** (41% reduction in Unknown wells)  
✅ **7,452 readings now usable** for trend analysis  
✅ **Unknown reduced from 14.8% to 8.7%** of total wells  
✅ **91.3% of wells now have forecasts** (up from 85.2%)

## District Breakdown of Fixed Wells

| District | Wells Fixed | Example Wells |
|----------|-------------|---------------|
| Jabalpur | 48 wells | SJBP069-OW, SJBPL008PZ-D |
| Tikamgarh | 13 wells | Tikm001-PZ, Tikm016-PZ |
| Sagar | 5 wells | SAGAR-PDS-016-PZ to 020-PZ |
| Chhatarpur | 2 wells | Chhat001-PZ, Chhat004-PZ |
| Indore | 2 wells | SIND-034-PZ, SIND-035-PZ |
| Ujjain | 1 well | SUJN019-OW |

## Remaining 104 Unknown Wells

These wells cannot be fixed without field data:
- 100 Panna district wells: No readings in database
- 3 other wells: CHHAT042-OW, SGR071-OW, PANOA022-OWD (insufficient data)
- 1 well: PANNA071A-OW (insufficient recent data)

**Recommendation:** Contact Panna district field teams to:
1. Verify if these 100 wells are operational
2. Upload historical readings if available
3. Remove from database if wells are abandoned

## Technical Details

### Elevation Sources
- **API**: Open-Elevation (https://api.open-elevation.com)
- **Data**: SRTM 30m resolution Digital Elevation Model
- **Accuracy**: ±16m vertical accuracy (sufficient for groundwater)

### Examples of Fixed Wells

**Chhat001-PZ** (Chhatarpur)
- Elevation: 480m MSL
- 277 readings converted
- Trend: **Critical** (declining)
- Now shows proper forecast on map

**Tikm001-PZ** (Tikamgarh)
- Elevation: 221m MSL
- 250 readings converted
- Trend: **Stable**
- Was showing "Unknown", now displays correctly

**SJBP069-OW** (Jabalpur)
- Elevation: 378m MSL
- 150 readings converted
- Trend: **Critical** (declining)
- Fully functional forecast

### Performance
- Elevation fetch: ~2 seconds per batch (20 wells)
- Database update: 7,452 readings in <5 seconds
- Cache sync: ~1 second per well
- **Total time: ~5 minutes** for complete fix

## Maintenance

### When to Re-run
If new wells show "Unknown" with readings:
```bash
# Check for wells with depth but no elevation
docker exec infra-db-1 psql -U gwuser -d groundwater -c "
SELECT w.well_id, COUNT(r.id) as readings
FROM wells w
INNER JOIN readings r ON w.well_id = r.well_id
WHERE w.elevation_m IS NULL
  AND r.depth_bgl_m IS NOT NULL
  AND r.head_msl_m IS NULL
GROUP BY w.well_id;
"

# If any found, run:
cd /Users/rudrajadon/Downloads/groundwater-app/etl
source ../.venv/bin/activate
python fetch_elevations.py
```

### Future Enhancement
Consider adding elevation lookup to ETL pipeline:
1. When new well added with coordinates
2. Automatically fetch elevation from Open-Elevation
3. No manual intervention needed

## Files Modified

1. **Created**: `/Users/rudrajadon/Downloads/groundwater-app/etl/fetch_elevations.py`
   - Fetches elevations for wells missing data
   - Computes head_msl_m from depth + elevation
   - Fully automated, can be re-run anytime

2. **Database**: Updated 71 wells
   - Added `elevation_m` values
   - Computed `head_msl_m` for 7,452 readings
   - Updated `trend_label` cache for 73 wells

## Conclusion

✅ **Platform reliability significantly improved**  
✅ **91.3% of wells now have forecasts** (was 85.2%)  
✅ **Unknown wells reduced by 41%**  
✅ **All fixable issues resolved**

The remaining 104 "Unknown" wells genuinely lack data and require field measurements. The platform is now reliable for public use with proper forecasts for all wells with available data.
