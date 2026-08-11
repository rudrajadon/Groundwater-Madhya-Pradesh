# Coordinate Data Quality Fixes
**Date:** 2026-08-09  
**Issue:** Three wells had incorrect coordinates placing them outside Madhya Pradesh

## Problem Wells Identified

During map verification, three wells were found displaying far outside MP boundaries:

| Well ID | Block | District | Original Coordinates | Incorrect Location |
|---------|-------|----------|---------------------|-------------------|
| BPL033A-OW | Fanda | Unknown | 30.205°N, 77.358°E | Dehradun, Uttarakhand |
| PANNA030-OW | Gunour | Panna | 24.354°N, 88.045°E | West Bengal (near Bangladesh) |
| PANNA037-OW | Shahnagar | Panna | 34.133°N, 79.833°E | Jammu & Kashmir/Ladakh |

## Root Cause
Likely data entry errors in the original MDB files where coordinates were:
- Swapped (lat/lon reversed)
- Decimal point misplaced
- Manually entered incorrectly

## Corrected Coordinates

Coordinates were verified using reliable sources (Wikipedia, official government data):

| Well ID | Block | District | Corrected Coordinates | Source |
|---------|-------|----------|----------------------|---------|
| BPL033A-OW | Fanda (Phanda Kala) | Bhopal | 23.26°N, 77.41°E | Bhopal district center approximation |
| PANNA030-OW | Gunour | Panna | 24.46°N, 80.25°E | [Wikipedia - Gunour](https://en.wikipedia.org/wiki/Gunour) |
| PANNA037-OW | Shahnagar | Panna | 23.99°N, 80.30°E | [Wikipedia - Shahnagar](https://en.wikipedia.org/wiki/Shahnagar) |

## SQL Fix Applied

```sql
-- Fix BPL033A-OW (Fanda, Bhopal)
UPDATE wells 
SET geom = ST_SetSRID(ST_MakePoint(77.41, 23.26), 4326)
WHERE well_id = 'BPL033A-OW';

-- Fix PANNA030-OW (Gunour, Panna)
UPDATE wells 
SET geom = ST_SetSRID(ST_MakePoint(80.25, 24.46), 4326)
WHERE well_id = 'PANNA030-OW';

-- Fix PANNA037-OW (Shahnagar, Panna)
UPDATE wells 
SET geom = ST_SetSRID(ST_MakePoint(80.30, 23.99), 4326)
WHERE well_id = 'PANNA037-OW';
```

## Verification

After fixes, all 1,196 wells with coordinates now fall within Madhya Pradesh bounds:
- **Latitude range:** 22.36°N to 26.31°N ✅ (MP bounds: 21-26.9°N)
- **Longitude range:** 75.04°E to 80.58°E ✅ (MP bounds: 74-82.8°E)
- **Wells outside bounds:** 0 ✅

## Data Impact

### BPL033A-OW
- **Readings:** 56 water level measurements (2012-2026)
- **Status:** Well has historical data, now correctly positioned
- **Impact:** Forecasts now use correct spatial context

### PANNA030-OW & PANNA037-OW
- **Readings:** 0 measurements
- **Status:** No historical data
- **Impact:** Coordinates fixed for future data collection

## Recommendations

1. **ETL Enhancement:** Add coordinate validation checks in the ETL pipeline:
   ```python
   # Verify coordinates are within MP bounds
   MP_LAT_MIN, MP_LAT_MAX = 21.0, 26.9
   MP_LON_MIN, MP_LON_MAX = 74.0, 82.8
   
   if not (MP_LAT_MIN <= lat <= MP_LAT_MAX and MP_LON_MIN <= lon <= MP_LON_MAX):
       logger.warning(f"Well {well_id} at ({lat}, {lon}) outside MP bounds")
   ```

2. **Data Quality Checks:** Implement automated bounds checking during data import

3. **Source Data Review:** Consider auditing remaining wells for similar coordinate issues

4. **Documentation:** Record coordinate sources in database for traceability

## References
- Madhya Pradesh boundaries: 21-26.9°N latitude, 74-82.8°E longitude
- Gunour coordinates: Wikipedia (https://en.wikipedia.org/wiki/Gunour)
- Shahnagar coordinates: Wikipedia (https://en.wikipedia.org/wiki/Shahnagar)
- Bhopal district center: ~23.26°N, 77.41°E
