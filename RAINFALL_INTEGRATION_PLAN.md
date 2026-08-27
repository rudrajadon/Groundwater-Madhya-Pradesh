# Rainfall Integration Plan
*MP Groundwater Monitor - IMD Rainfall Data Integration*

---

## 📋 Overview

Integrating 75 years (1950-2024) of IMD gridded rainfall data into the MP Groundwater Monitor to improve ML model accuracy and enable rainfall-groundwater correlation analysis.

**Status**: ✅ Task #2 in progress - Rainfall extraction script running

---

## 🎯 Goals

1. **Improve ML Model Accuracy**
   - Current R²: 0.65 → Target R²: 0.70-0.75
   - Current RMSE: 3.40m → Target RMSE: 2.8-3.0m
   - Better monsoon prediction and recharge modeling

2. **Enable Correlation Analysis**
   - Quantify rainfall-groundwater lag (1-6 months)
   - Identify recharge-efficient vs recharge-deficient regions
   - Seasonal pattern analysis

3. **Enhance Visualization**
   - Add rainfall layer to interactive map
   - Create rainfall-groundwater comparison dashboard
   - Show recharge events and their impact

4. **Database Integration**
   - Store rainfall data for API access
   - Enable district/well-level rainfall queries
   - Historical rainfall trends

---

## 📊 Data Source

### IMD Gridded Rainfall Data
- **Source**: India Meteorological Department (IMD)
- **Format**: NetCDF (.nc files)
- **Resolution**: 0.25° × 0.25° (~25 km grid)
- **Temporal Coverage**: 1950-2024 (75 years)
- **Temporal Resolution**: Daily
- **Variables**: Rainfall (mm/day)
- **Geographic Coverage**: All India (6.5°N - 38.5°N, 66.5°E - 100.0°E)

### MP Region Coverage
- **Latitude**: 21.0°N to 26.5°N (23 grid cells)
- **Longitude**: 74.0°E to 82.5°E (35 grid cells)
- **Total Grid Cells**: 805
- **Wells in MP**: 1,193

---

## 🔧 Implementation Tasks

### ✅ Task 1: Baseline Model Analysis
**Status**: Complete  
**Output**: `ml/BASELINE_MODEL_ANALYSIS.md`

**Key Findings:**
- Model: PGNN-LSTM with 144,708 parameters
- Performance: R² 0.65, RMSE 3.40m, MAE 2.8m
- Architecture: 2-layer GCN + 4 geology-stratified LSTMs
- Limitations: No rainfall data, unused features

### 🔄 Task 2: Rainfall Extraction
**Status**: In Progress (Running)  
**Script**: `etl/extract_rainfall_for_wells.py`  
**Terminal**: term_1787847570788_hurva4bo6og

**Progress:**
- ✅ Loaded 1,193 wells from CSV
- ✅ Built KD-tree spatial index (17,415 grid cells)
- 🔄 Extracting rainfall data (1950-2024)
- Processing ~90,000 well-years of data

**Output:**
- File: `data/rainfall_well_monthly.csv`
- Columns: well_id, year, month, rainfall_mm, lat, lon, district, geology_type
- Expected records: ~1,193 wells × 75 years × 12 months = 1,073,700 rows

**Method:**
1. Read NetCDF files year by year
2. For each well: find nearest grid cell using KD-tree
3. Aggregate daily rainfall to monthly totals
4. Save with well metadata

### 📊 Task 3: Correlation Analysis
**Status**: Not Started  
**Script**: `etl/analyze_rainfall_groundwater_correlation.py` (to be created)

**Planned Analysis:**
1. **Pearson Correlation**
   - Well-by-well correlation (rainfall vs water level)
   - District-level aggregated correlation
   - Aquifer-type stratified correlation

2. **Lag Analysis**
   - Test lags: 0, 1, 2, 3, 4, 5, 6 months
   - Identify optimal lag per well
   - Regional lag patterns (basalt vs granite)

3. **Seasonal Decomposition**
   - Separate trend, seasonal, residual components
   - Monsoon impact quantification
   - Dry season decline rates

4. **Recharge Efficiency**
   - Rainfall → groundwater conversion rate
   - Identify high-efficiency and low-efficiency zones
   - Geology-specific recharge coefficients

**Output:**
- Report: `data/rainfall_gw_correlation_report.md`
- Data: `data/correlation_results.csv`
- Plots: `data/plots/correlation_*.png`

### 🧠 Task 4: Update ML Model
**Status**: Not Started  
**Files**: `ml/model.py`, `ml/preprocessing.py`

**Changes Required:**

#### 4a. Update Node Features (model.py)
```python
# Current: 8 features
# [lat, lon, elev, cmd, weathered%, fractured%, massive%, depth]

# New: 9 features (add rainfall stats)
# [lat, lon, elev, cmd, weathered%, fractured%, massive%, depth, avg_rainfall_5y]
n_node_feat = 9  # was 8
```

#### 4b. Update Sequence Input (preprocessing.py)
```python
# Current: [B, 24, 1] - water level only
# New: [B, 24, 2] - water level + rainfall

# Sequence structure:
# [:, :, 0] = water level (m MSL)
# [:, :, 1] = rainfall (mm/month, normalized)

lstm_in = 2 + gcn_h  # was 1 + gcn_h
```

#### 4c. Add Rainfall Preprocessing
```python
def load_rainfall_sequences(wells, rainfall_df, seq_len=24):
    """
    Create rainfall sequences aligned with water level sequences.
    Handle missing data with interpolation or district average.
    """
    pass
```

#### 4d. Update Training Pipeline
- Load rainfall data alongside water level data
- Normalize rainfall per well (MinMax or Z-score)
- Create paired sequences (water_level, rainfall)
- Update data loaders

### 🔄 Task 5: Retrain Model
**Status**: Not Started  
**Script**: `ml/train.py` (already exists, needs data update)

**Training Strategy:**
1. Use same hyperparameters as baseline
2. Track metrics separately:
   - Baseline (no rainfall): R² 0.65
   - With rainfall: R² 0.?? (target 0.70-0.75)
3. Ablation study:
   - Rainfall-only model
   - Water-level-only model (baseline)
   - Combined model
4. Cross-validation by year (2020-2024 hold-out)

**Expected Training Time:**
- Similar to baseline: ~60-90 minutes on CPU
- 150 epochs max, early stopping

**Metrics to Track:**
- RMSE (overall and per-month)
- MAE (median error)
- R² (variance explained)
- Physics loss components
- Performance by aquifer type
- Performance by season (monsoon vs dry)

### 💾 Task 6: Database Integration
**Status**: Not Started  
**Script**: `etl/load_rainfall_to_postgres.py` (to be created)

**Database Schema:**
```sql
CREATE TABLE rainfall (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    rainfall_mm REAL,
    source VARCHAR(20) DEFAULT 'IMD_0.25deg',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(well_id, date),
    FOREIGN KEY (well_id) REFERENCES wells(well_id)
);

CREATE INDEX idx_rainfall_well_date ON rainfall(well_id, date);
CREATE INDEX idx_rainfall_date ON rainfall(date);
```

**Loading Process:**
1. Read `rainfall_well_monthly.csv`
2. Convert year/month to date (YYYY-MM-01)
3. Bulk insert using COPY command
4. Create indexes for fast queries
5. Verify data integrity

**Expected Size:**
- ~1M rows × 50 bytes/row = ~50 MB
- With indexes: ~100 MB

### 🔌 Task 7: API Endpoints
**Status**: Not Started  
**File**: `backend/app/routers/rainfall.py` (to be created)

**New Endpoints:**

#### GET /api/v1/rainfall/{well_id}
```json
{
  "well_id": "BPL050-OW",
  "data": [
    {"date": "2020-01", "rainfall_mm": 5.2},
    {"date": "2020-02", "rainfall_mm": 12.4},
    ...
  ],
  "stats": {
    "mean": 89.3,
    "median": 45.2,
    "annual_avg": 1071.6
  }
}
```

#### GET /api/v1/rainfall/district/{district}
```json
{
  "district": "Bhopal",
  "wells_count": 156,
  "monthly_avg": [
    {"month": 1, "rainfall_mm": 15.2},
    {"month": 2, "rainfall_mm": 18.4},
    ...
  ]
}
```

#### GET /api/v1/rainfall/correlation/{well_id}
```json
{
  "well_id": "BPL050-OW",
  "correlation": 0.62,
  "optimal_lag_months": 2,
  "recharge_efficiency": 0.15
}
```

### 🗺️ Task 8: Map Visualization
**Status**: Not Started  
**File**: `frontend/components/RainfallLayer.tsx` (to be created)

**Features:**
1. **Toggle Button**
   - "Show Rainfall" / "Hide Rainfall"
   - Settings menu integration

2. **Heatmap Overlay**
   - Color-coded rainfall intensity
   - District-level aggregation
   - Month slider (animate through time)

3. **Well Popup Enhancement**
   - Add rainfall chart to popup
   - Show correlation coefficient
   - Rainfall-groundwater dual axis chart

4. **Time Series Player**
   - Play/pause animation
   - Speed control
   - Year range selector

### 📊 Task 9: Comparison Dashboard
**Status**: Not Started  
**File**: `frontend/pages/rainfall-analysis.tsx` (to be created)

**Components:**

#### 1. Dual-Axis Time Series
```
Rainfall (bars) ┬─────────────────────────
                │ ████ ██████████ ████
                │
Groundwater ────┼─────────────────────────
(line)          │     ╱╲      ╱╲     ╱╲
                │    ╱  ╲    ╱  ╲   ╱  ╲
                └─────────────────────────
```

#### 2. Correlation Heatmap
- Districts × Months
- Color intensity = correlation strength
- Interactive tooltips

#### 3. Recharge Efficiency Map
- Chloropleth by district
- Rainfall → groundwater conversion rate
- Best/worst performers

#### 4. Seasonal Analysis
- Monsoon vs dry season comparison
- Water level response to rainfall events
- Lag distribution histogram

### 📝 Task 10: Documentation
**Status**: Not Started  

**Files to Update:**
1. `README.md`
   - Add rainfall integration section
   - Update model metrics
   - Add new API endpoints

2. `FAQ.md`
   - Add rainfall-related questions
   - Explain correlation analysis
   - Data sources and reliability

3. `PROJECT_STRUCTURE.md`
   - Add rainfall components
   - Update data flow diagram
   - Database schema updates

4. `docs/API_CONTRACT.md`
   - Document new rainfall endpoints
   - Request/response examples
   - Rate limiting notes

### ✅ Task 11: Testing
**Status**: Not Started  

**Test Plan:**

#### Unit Tests
- Rainfall extraction logic
- Correlation calculations
- Database queries
- API endpoint responses

#### Integration Tests
- End-to-end data flow
- ML model with rainfall input
- Frontend-backend communication

#### Performance Tests
- API response times (<500ms)
- Database query optimization
- Map rendering with rainfall layer

#### Data Quality Tests
- Rainfall data completeness
- Outlier detection
- Correlation sanity checks

---

## 📈 Expected Improvements

### Model Performance
| Metric | Baseline | With Rainfall | Improvement |
|--------|----------|---------------|-------------|
| R² Score | 0.65 | 0.70-0.75 | +7-15% |
| RMSE (m) | 3.40 | 2.8-3.0 | -12-18% |
| MAE (m) | 2.8 | 2.3-2.5 | -11-18% |

### Specific Improvements
1. **Monsoon Prediction**: +20-30% accuracy
2. **Recharge Events**: Better capture of sudden water level rise
3. **Dry Season**: More accurate decline rates
4. **Spatial Generalization**: Better predictions in data-sparse regions

---

## ⚠️ Challenges & Solutions

### Challenge 1: Large Data Volume
- **Issue**: 1M+ rows of rainfall data
- **Solution**: 
  - PostgreSQL indexing
  - API pagination
  - Frontend data aggregation
  - Caching frequently accessed data

### Challenge 2: Missing Data
- **Issue**: Some wells may have incomplete rainfall coverage
- **Solution**:
  - Interpolation from nearest grid cells
  - District-level averages as fallback
  - Mark low-confidence predictions

### Challenge 3: Computational Cost
- **Issue**: Retraining model takes ~60-90 minutes
- **Solution**:
  - Use existing infrastructure (CPU-optimized)
  - Incremental training (future)
  - Model versioning

### Challenge 4: Rainfall-Groundwater Lag
- **Issue**: Lag varies by location and aquifer type
- **Solution**:
  - Well-specific lag estimation
  - Geology-stratified lag models
  - Adaptive lag in LSTM (attention mechanism handles this)

---

## 📅 Timeline Estimate

| Task | Duration | Dependencies |
|------|----------|--------------|
| 1. Baseline Analysis | ✅ 1 hour | None |
| 2. Rainfall Extraction | 🔄 2-3 hours | Task 1 |
| 3. Correlation Analysis | 2 hours | Task 2 |
| 4. Update ML Model | 3 hours | Task 2, 3 |
| 5. Retrain Model | 1.5 hours | Task 4 |
| 6. Database Integration | 1 hour | Task 2 |
| 7. API Endpoints | 2 hours | Task 6 |
| 8. Map Visualization | 3 hours | Task 7 |
| 9. Comparison Dashboard | 4 hours | Task 7 |
| 10. Documentation | 2 hours | All tasks |
| 11. Testing | 3 hours | All tasks |

**Total Estimated Time**: 24-26 hours

**Current Progress**: ~3 hours completed (Tasks 1-2)

---

## 🎯 Success Criteria

### Quantitative
- ✅ R² improvement: ≥0.05 (from 0.65 to ≥0.70)
- ✅ RMSE reduction: ≥0.4m (from 3.40m to ≤3.0m)
- ✅ Rainfall data coverage: ≥95% of wells
- ✅ API response time: <500ms for rainfall queries
- ✅ Correlation coefficients: meaningful (|r| > 0.3) for ≥70% of wells

### Qualitative
- ✅ Improved monsoon prediction accuracy
- ✅ Better capture of recharge events
- ✅ Clear visualization of rainfall-groundwater relationship
- ✅ Actionable insights for water resource managers
- ✅ Comprehensive documentation

---

## 📚 References

1. **IMD Gridded Rainfall Data**
   - Source: India Meteorological Department
   - Documentation: [IMD Website](https://www.imdpune.gov.in/)

2. **Groundwater-Rainfall Correlation Studies**
   - Typical lag: 1-3 months in hard rock aquifers
   - Recharge efficiency: 10-25% in Deccan basalt

3. **PGNN-LSTM Architecture**
   - Spatial learning: GCN captures well correlations
   - Temporal learning: LSTM handles seasonal patterns
   - Physics-guided: Darcy's law constraints

---

*Generated: 2025-08-27*  
*Last Updated: Task 2 in progress*  
*Author: Rudra Pratap Singh Jadon*
