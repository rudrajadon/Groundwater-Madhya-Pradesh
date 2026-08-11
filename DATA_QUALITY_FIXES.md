# Data Quality Fixes - August 8, 2026

## Issues Identified and Fixed

### 1. ✅ Invalid Confidence Scores (>1.0)
**Problem**: 14 wells had confidence scores exceeding 1.0 (max 1.4), violating the standard 0.0-1.0 range.

**Root Cause**: Original classification script accumulated keyword matches across all lithology layers without proper normalization. Example: a well with 3 layers, each mentioning "basalt" multiple times, could get score=4, confidence=4/3=1.33.

**Fix**: Implemented normalized confidence calculation in `etl/fix_data_quality.py`:
```python
# Now: confidence = fraction of layers matching (capped at 1.0)
basalt_layers = sum(1 for layer in well_litho if any(kw in layer for kw in BASALT_KEYWORDS))
confidence = min(basalt_layers / total_layers, 1.0)
```

**Result**: All 1,196 wells now have confidence ≤ 1.0 (mean=0.61, max=1.0, min=0.0)

---

### 2. ✅ Well ID Formatting Issues
**Problem**: 
- 3 wells used '0' (zero) instead of 'O' (letter): `BPL053A-0W`, `PANNA053-0W`, `TKM032-0W`
- 51 wells contained spaces
- Inconsistent capitalization (mixed case)

**Fix**: Implemented `fix_well_id()` function with:
1. Replace `-0W` → `-OW` (typo correction)
2. Remove all spaces
3. Standardize to UPPERCASE

**Result**: All well IDs now follow consistent format: `{DISTRICT}{NUMBER}{VARIANT}-{TYPE}`
- Example: `BPL053A-0W` → `BPL053A-OW`
- Updated in: `data/wells.csv`, `data/litho.csv`, `data/water_levels.csv` (139,837 records)

---

### 3. ✅ Aquifer Classification Imbalance
**Problem**: 89.7% wells classified as Weathered, only 1.4% Fractured - unrealistic distribution.

**Root Cause**: Original logic used OR condition: `if depth ≤30m OR has_weathered_keyword` → defaults to Weathered too aggressively.

**Fix**: Implemented stricter classification logic:
```python
# Weathered: depth ≤30m AND has weathered keywords
# Fractured: depth >30m AND <150m AND (has fracture keywords OR no weathered keywords)
# Deep wells (>150m): classified as Fractured (typical for deep borewells)
```

**Result**: More realistic distribution:
- **Before**: Weathered 1,073 (89.7%), Fractured 17 (1.4%), Unknown 106 (8.9%)
- **After**: Weathered 887 (74.2%), Fractured 77 (6.4%), Unknown 232 (19.4%)

Fractured wells increased 4.5×, reflecting deeper borewells correctly classified.

---

### 4. ⚠️ Panna & Jabalpur Missing/Unknown Geology
**Problem**: Large sections filled with Unknown values and 0.0 confidence:
- Panna: 105/105 wells Unknown
- Jabalpur: 62/131 wells Unknown

**Fix Applied**: 
1. Expanded geology keywords to include regional synonyms:
   - Basalt: added `'volcanic', 'black soil', 'regur', 'cotton soil'`
   - Granite: added `'feldsp', 'quartz', 'mica', 'igneous', 'metamorphic'`
   - Vindhyan: added `'sand', 'clay', 'gravel', 'pebble', 'boulder'`
2. Improved keyword matching algorithm

**Result**:
- **Jabalpur**: 62 → 30 Unknown (52% improvement ✅)
- **Panna**: 105 → 103 Unknown (1.9% improvement ⚠️)

**Remaining Issue - Panna District**:
After investigation, the 103 Unknown Panna wells are a **data availability limitation**, not a classification bug:

```
Wells.csv:    PANNA001A-OW, PANNA002A-OW, ... (observation wells)
Litho.csv:    PANNA-PZ-01, PANNA-PZ-02, ... (piezometers)
```

The 106 observation wells (OW) in wells.csv have **no matching lithology data** in litho.csv, which only contains 3 piezometer records (PZ). These are different well types at different locations.

**Options to Address**:
1. **Source original lithology data** for PANNA-OW wells from the Access databases in `GW_Data/Water Level/Spannaow.Mdb` or `GW_Data/Water Level/sPannaPZ.mdb`
2. **Use district-level geology** to assign Panna wells to "Vindhyan" based on regional geology (lower confidence, requires domain expert approval)
3. **Leave as Unknown** and document as data limitation (current approach)

---

## Summary Statistics (After Fixes)

### Geology Distribution
| Type     | Count | Percentage |
|----------|-------|------------|
| Basalt   | 590   | 49.3%      |
| Granite  | 236   | 19.7%      |
| Vindhyan | 231   | 19.3%      |
| Unknown  | 139   | 11.6%      |

### Aquifer Distribution
| Type      | Count | Percentage |
|-----------|-------|------------|
| Weathered | 887   | 74.2%      |
| Fractured | 77    | 6.4%       |
| Unknown   | 232   | 19.4%      |

### Data Quality Metrics
- **Confidence scores**: 0 wells >1.0 ✅
- **Well ID format**: 1,196/1,196 standardized ✅
- **Lithology coverage**: 1,057/1,196 (88.4%) ✅
- **Panna coverage**: 3/106 (2.8%) ⚠️ (data limitation)

---

## Recommendations

### Immediate Actions
1. ✅ **Deploy fixes**: Database updated with corrected classifications
2. ✅ **Validate frontend**: Popups now show correct geology/aquifer data

### Future Improvements
1. **Extract Panna lithology**: Parse `Spannaow.Mdb` to add missing lithology data for 103 wells
2. **Class balancing for ML**: Current 74% Weathered / 6% Fractured imbalance may require:
   - SMOTE (Synthetic Minority Over-sampling Technique) for Fractured class
   - Collect more deep borewell data from field surveys
   - Stratified sampling during model training
3. **Confidence thresholds**: Consider flagging wells with confidence <0.3 as "Low Quality" in UI

---

## Files Modified
1. `etl/fix_data_quality.py` - New comprehensive fix script
2. `data/wells.csv` - Updated well IDs and classifications
3. `data/litho.csv` - Standardized well IDs
4. `data/water_levels.csv` - Standardized well IDs (139,837 records)
5. `data/well_geology_classifications.csv` - Recalculated with fixed logic
6. Database `wells` table - Updated via `etl/update_database_geology.py`

---

**Date**: August 8, 2026  
**Script**: `etl/fix_data_quality.py`  
**Database**: Updated via `etl/update_database_geology.py`
