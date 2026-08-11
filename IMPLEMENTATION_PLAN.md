# Critical Implementation Issues & Action Plan

## 🚨 Problems Identified

### 1. **Missing Lithology/Rock Type Data**
**Current State:**
- `data/litho.csv` is EMPTY (only header row)
- Wells don't have geology classification (Basalt/Granite/Vindhyan)
- UI shows "NaN" or nothing for aquifer_zone

**Required:**
- Extract lithology data from .mdb files
- Classify wells by geology type: Basalt, Granite, Vindhyan
- Display rock type in well popups and details

### 2. **Wrong Forecasting Model**
**Current State:**
- Using simple linear regression (`statistical_trend.py`)
- No graph neural network
- No LSTM component
- No physics constraints

**Required (from PGNN_LSTM_Final notebook):**
- PGNN-LSTM model with 6-branch geology classification
- Graph structure based on spatial proximity
- LSTM for temporal sequences
- Physics-guided loss (Darcy's law + water balance)
- Rainfall integration (WRIS data)

### 3. **Missing Key Features**
According to the presentation slides, the app should have:
- ❌ 6-branch geology classification (Basalt/Granite/Vindhyan)
- ❌ PGNN-LSTM model
- ❌ Rainfall data integration
- ❌ Physics engine (Darcy-law GCN + FD baseline)
- ❌ Uncertainty bands
- ❌ MP Stress Map (risk zones across all districts)
- ❌ Alert list (critical wells needing action)
- ❌ Policy PDF/CSV export

**Currently working:**
- ✅ Interactive map
- ✅ Basic forecasting (wrong model)
- ✅ Historical charts
- ✅ Docker deployment

---

## 📋 Action Plan

### Phase 1: Data Extraction & Geology Classification ⏰ 2-3 hours

#### Task 1.1: Extract Lithology Data from .mdb Files
```bash
# Need to extract from tables like:
# - Lithology, LITHO, Well_Litho, Strata, Formation
# Using mdb-export or mdbtools
```

**Steps:**
1. Scan all 21 .mdb files for lithology tables
2. Extract depth ranges and rock descriptions
3. Create comprehensive `litho.csv` with columns:
   - well_id, depth_from_m, depth_to_m, lithology, color, texture
4. Parse lithology keywords to classify geology type

#### Task 1.2: Classify Wells by Geology
Based on PGNN notebook logic:
```python
# Classification rules from notebook:
# 1. Basalt: "basalt", "trap", "vesicular" keywords
# 2. Granite: "granite", "gneiss", "crystalline" keywords  
# 3. Vindhyan: "sandstone", "shale", "limestone", "vindhyan" keywords
# 4. Use depth rules: weathered (0-30m), fractured (30-100m), massive (>100m)
```

**Output:**
- Update `wells.csv` with `geology_type` column
- Populate `aquifer_zone` with weathered/fractured/massive classification

#### Task 1.3: Update Database Schema
```sql
ALTER TABLE wells ADD COLUMN geology_type TEXT; -- Basalt/Granite/Vindhyan
ALTER TABLE wells ADD COLUMN aquifer_classification TEXT; -- Weathered/Fractured/Massive
UPDATE wells SET geology_type = ... (from litho analysis)
```

---

### Phase 2: PGNN-LSTM Model Implementation ⏰ 1-2 days

#### Task 2.1: Read and Understand PGNN_LSTM_Final notebook
**Key sections to extract:**
1. Data preprocessing
   - BGL → Hydraulic head conversion ✅ (already doing this)
   - Rainfall feature engineering (7 features: current + 3 lags)
   - Aquifer classification logic
   - Graph construction (spatial edges)

2. Model architecture
   - Graph Convolutional layers
   - LSTM for temporal sequences
   - 6-branch geology-specific processing
   - Output: monthly forecasts to 2040

3. Physics-guided loss
   - Water balance constraint
   - Darcy's law incorporation
   - Loss = MSE + λ_physics * physics_loss

4. Training procedure
   - Train/val/test split
   - Hyperparameters
   - Model checkpoints

#### Task 2.2: Implement PGNN-LSTM in `backend/app/services/`
Create new files:
```
backend/app/services/
├── pgnn_lstm_model.py      # Model architecture
├── graph_builder.py         # Construct spatial graph
├── physics_constraints.py   # Darcy + water balance
├── rainfall_features.py     # Rainfall integration
└── model_inference.py       # Load model & predict
```

#### Task 2.3: Train the Model
```bash
# In ml/ directory:
python train_pgnn_lstm.py \
  --data data/wells.csv data/water_levels.csv data/litho.csv \
  --rainfall data/rainfall.csv \
  --output ml/artifacts/pgnn_lstm_best.pt
```

**Training requirements:**
- GPU recommended (but can run on CPU)
- ~1-2 hours training time
- Validation on hold-out wells
- Save model + scalers + graph structure

#### Task 2.4: Integrate Model into Backend
```python
# backend/app/services/forecast.py
def get_forecast_pgnn(well_id):
    # Load PGNN-LSTM model
    # Fetch recent readings + rainfall
    # Build graph features
    # Run inference
    # Return 12-month forecast with uncertainty
```

---

### Phase 3: Rainfall Data Integration ⏰ 3-4 hours

#### Task 3.1: Fetch Historical Rainfall Data
Options:
1. **WRIS (Water Resources Information System)** - Government data
2. **Open-Meteo API** - Already have script: `etl/fetch_rainfall_openmeteo.py`
3. **IMD (India Meteorological Department)** - Official source

**Recommended:** Use Open-Meteo for now (free, reliable)

```bash
python etl/fetch_rainfall_openmeteo.py \
  --wells data/wells.csv \
  --start-date 1976-01-01 \
  --end-date 2024-12-31 \
  --output data/rainfall.csv
```

#### Task 3.2: Process Rainfall Features
From PGNN notebook, need 7 features per month:
1. Current month rainfall (mm)
2. Lag-1 (previous month)
3. Lag-2 (2 months ago)
4. Lag-3 (3 months ago)
5. Cumulative 3-month
6. Cumulative 6-month
7. Annual average

#### Task 3.3: IDW Interpolation
Assign rainfall to each well using Inverse Distance Weighting:
```python
def assign_rainfall_to_wells(wells_df, rain_stations_df):
    # For each well:
    #   Find 3 nearest rain stations
    #   Compute IDW weights (1/distance^2)
    #   Interpolate rainfall value
```

---

### Phase 4: UI Enhancements ⏰ 2-3 hours

#### Task 4.1: Display Geology Type in Well Popups
```tsx
// frontend/components/Map.tsx
<Popup>
  <strong>{well_id}</strong>
  <br />
  {block}
  {geology_type && (
    <>
      <br />
      🪨 {geology_type} - {aquifer_classification}
    </>
  )}
</Popup>
```

#### Task 4.2: Add Geology Legend to Map
```tsx
<div className="map-legend">
  <div>🔵 Basalt (290 wells)</div>
  <div>🟣 Granite (225 wells)</div>
  <div>🟢 Vindhyan (61 wells)</div>
</div>
```

#### Task 4.3: Show Aquifer Type in Sidebar
```tsx
<div className="well-info-card">
  <h3>{well_id}</h3>
  <p>{block}</p>
  <div className="geology-info">
    <span className="geology-badge">{geology_type}</span>
    <span className="aquifer-badge">{aquifer_classification}</span>
  </div>
</div>
```

---

### Phase 5: Additional Features (Future) ⏰ 3-5 days

#### Task 5.1: MP Stress Map
- Aggregate well status by district
- Create choropleth map showing % critical wells
- Color districts by risk level

#### Task 5.2: Alert List
- Filter wells where forecast shows >5m decline by 2040
- Generate CSV export
- Email alerts (optional)

#### Task 5.3: Export Functionality
- PDF report generation
- CSV data export
- Policy brief format

#### Task 5.4: Uncertainty Visualization
- Show confidence bands on forecast chart
- Explain conformal prediction approach
- Display model confidence score

---

## 🎯 Immediate Next Steps (Priority Order)

### Step 1: Extract Lithology Data (START HERE)
```bash
# Check what tables exist in .mdb files
for f in GW_Data/Water\ Level/*.mdb; do
    echo "=== $f ==="
    mdb-tables "$f" | grep -i "litho\|strata\|formation"
done

# Extract litho tables
# ... (detailed extraction commands)
```

### Step 2: Verify Notebook Requirements
- Read through entire PGNN_LSTM_Final notebook
- Document exact input format expected
- List all dependencies (torch, torch_geometric, etc.)

### Step 3: Quick Win - Show Available Geology Data
Even before PGNN-LSTM, we can:
1. Extract and display rock types from litho.csv
2. Update UI to show geology information
3. Improve user experience immediately

### Step 4: Plan PGNN-LSTM Migration Path
- Current: statistical model works
- Short-term: Hybrid (statistical + show geology)
- Long-term: Full PGNN-LSTM model

---

## 📊 Expected Outcomes

### After Phase 1 (Data + Geology):
```
Wells with geology classification:
├── Basalt: ~290 wells (Deccan Trap)
├── Granite: ~225 wells (Hard rock)
└── Vindhyan: ~61 wells (Sedimentary)

UI shows:
├── Rock type in well popup
├── Aquifer classification (weathered/fractured/massive)
└── Color-coded by geology type
```

### After Phase 2 (PGNN-LSTM):
```
Forecasting:
├── Graph Neural Network with spatial relationships
├── LSTM for temporal patterns
├── Physics-guided constraints
├── Geology-specific processing (6 branches)
└── Uncertainty quantification

Output:
├── Monthly forecasts to 2040
├── Confidence intervals
├── Physics-compliant predictions
```

### After Phase 3 (Rainfall):
```
Additional features:
├── Monthly rainfall data (1976-2024)
├── 7 rainfall features per well
├── Improved forecast accuracy
└── Seasonal pattern recognition
```

---

## 🚧 Challenges & Risks

### Technical Challenges:
1. **Lithology extraction** - .mdb files may have inconsistent schemas
2. **PGNN-LSTM complexity** - Need PyTorch + torch_geometric
3. **Training time** - May need GPU for reasonable training time
4. **Model size** - PyTorch model may be large (~50-100MB)

### Data Challenges:
1. **Missing litho data** - Not all wells may have lithology records
2. **Rainfall coverage** - Need station data or API access
3. **Data quality** - Inconsistent formats across districts

### Deployment Challenges:
1. **Docker image size** - Adding PyTorch increases image size
2. **Inference speed** - PGNN-LSTM slower than statistical model
3. **Model serving** - Need to load model on backend startup

---

## 🔧 Tools & Dependencies

### New Python Packages Needed:
```txt
# For PGNN-LSTM
torch>=2.0.0
torch-geometric>=2.3.0
torch-scatter
torch-sparse
scikit-learn
shap  # for model explainability

# For data processing
pyarrow  # for efficient data loading
```

### New Scripts to Create:
1. `etl/extract_lithology.py` - Extract from .mdb
2. `etl/classify_geology.py` - Classify wells by rock type
3. `ml/train_pgnn_lstm.py` - Train the model
4. `ml/model_pgnn_lstm.py` - Model architecture
5. `backend/app/services/pgnn_inference.py` - Use model for predictions

---

## 📅 Estimated Timeline

### Aggressive (if focused):
- Phase 1: 4-6 hours
- Phase 2: 2-3 days
- Phase 3: 4-6 hours
- Phase 4: 3-4 hours
- **Total: 4-5 days**

### Realistic (with testing):
- Phase 1: 1 day
- Phase 2: 4-5 days
- Phase 3: 1 day
- Phase 4: 1 day
- Testing & fixes: 2 days
- **Total: 9-10 days**

---

## ✅ Success Criteria

The implementation will be considered complete when:

1. ✅ All wells have geology classification (Basalt/Granite/Vindhyan)
2. ✅ UI displays rock type and aquifer classification
3. ✅ PGNN-LSTM model trained and deployed
4. ✅ Forecasts match notebook results (validation metrics)
5. ✅ Rainfall data integrated
6. ✅ Physics constraints enforced
7. ✅ Uncertainty bands displayed
8. ✅ Performance acceptable (<5s per forecast)
9. ✅ Documentation updated
10. ✅ All tests passing

---

**Next Action:** Extract lithology data from .mdb files

Would you like me to start with Task 1.1 (extracting lithology data)?
