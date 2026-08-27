# Testing Guide
*MP Groundwater Monitor - Rainfall Integration Testing*

## Overview

This guide covers testing for the rainfall integration features.

---

## 1. Data Quality Tests

### **Rainfall Extraction**
```bash
cd /Users/rudrajadon/Downloads/groundwater-app

# Verify output file
ls -lh data/rainfall_well_monthly.csv

# Check record count (should be ~1M)
wc -l data/rainfall_well_monthly.csv

# Inspect sample data
head -20 data/rainfall_well_monthly.csv

# Statistics
python << EOF
import pandas as pd
df = pd.read_csv('data/rainfall_well_monthly.csv')
print(f"Records: {len(df):,}")
print(f"Wells: {df['well_id'].nunique()}")
print(f"Years: {df['year'].min()} - {df['year'].max()}")
print(f"\nRainfall Stats:")
print(df['rainfall_mm'].describe())
EOF
```

**Expected Results:**
- ✅ File size: ~68 MB
- ✅ Records: 1,045,068
- ✅ Wells: 1,193
- ✅ Years: 1950-2023
- ✅ Mean rainfall: ~85.7 mm/month

---

## 2. Database Tests

### **Load Data to PostgreSQL**
```bash
# Start database
cd infra
docker-compose up -d db

# Wait for database to be ready
sleep 10

# Load rainfall data
cd ..
source .venv/bin/activate
python etl/load_rainfall_to_postgres.py
```

**Verification:**
```bash
# Connect to database
docker-compose exec db psql -U gwuser -d groundwater

# Check record count
SELECT COUNT(*) FROM rainfall;
-- Expected: 1,045,068

# Check date range
SELECT MIN(date), MAX(date) FROM rainfall;
-- Expected: 1950-01-01 to 2023-12-01

# Sample query
SELECT well_id, date, rainfall_mm 
FROM rainfall 
WHERE well_id = 'BPL050-OW' 
ORDER BY date DESC 
LIMIT 10;

# Exit
\q
```

---

## 3. API Endpoint Tests

### **Start Backend**
```bash
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### **Test Endpoints**

**1. Get Well Rainfall:**
```bash
curl http://localhost:8000/api/v1/rainfall/BPL050-OW | jq
```

**Expected Response:**
```json
{
  "well_id": "BPL050-OW",
  "data": [
    {"date": "2023-12-01", "rainfall_mm": 5.2},
    {"date": "2023-11-01", "rainfall_mm": 8.7}
  ],
  "stats": {
    "mean": 85.71,
    "median": 9.36,
    "annual_avg": 1028.5
  }
}
```

**2. District Rainfall:**
```bash
curl http://localhost:8000/api/v1/rainfall/district/Bhopal | jq
```

**3. Correlation Metrics:**
```bash
curl http://localhost:8000/api/v1/rainfall/correlation/BPL050-OW | jq
```

**Performance Test:**
```bash
# Response time should be < 500ms
time curl -s http://localhost:8000/api/v1/rainfall/BPL050-OW > /dev/null
```

---

## 4. Frontend Tests

### **Start Frontend**
```bash
cd frontend
npm run dev
```

### **Manual Testing**

1. **Map Visualization:**
   - Open http://localhost:3000
   - Toggle rainfall layer (if implemented)
   - Verify wells display rainfall colors
   - Check popup shows rainfall data

2. **Rainfall Analysis Page:**
   - Navigate to http://localhost:3000/rainfall-analysis
   - Select different wells
   - Verify charts render correctly
   - Check correlation metrics display

3. **Responsive Design:**
   - Test on desktop (1920x1080)
   - Test on tablet (768px width)
   - Test on mobile (375px width)

4. **Dark Mode:**
   - Toggle dark mode in settings
   - Verify all components render properly
   - Check chart colors are visible

---

## 5. Integration Tests

### **End-to-End Flow**

**Scenario: View well rainfall data**
```
1. User opens map
2. Clicks well marker
3. Views well details popup
4. Sees historical rainfall chart
5. Clicks "View Analysis"
6. Sees rainfall-groundwater comparison
```

**Test Script:**
```javascript
// Cypress test (if implemented)
describe('Rainfall Integration', () => {
  it('displays rainfall data for well', () => {
    cy.visit('/')
    cy.get('[data-testid="well-marker-BPL050-OW"]').click()
    cy.contains('Rainfall').should('be.visible')
    cy.get('[data-testid="rainfall-chart"]').should('exist')
  })
})
```

---

## 6. Model Tests

### **Architecture Verification**
```bash
cd ml
python << EOF
import torch
from model import PGNN_LSTM

# Test model with rainfall input
model = PGNN_LSTM(n_node_feat=9, use_rainfall=True)
print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")

# Test forward pass
wl_seq = torch.randn(32, 24, 2)  # [batch, seq_len, 2 channels]
node_f = torch.randn(1196, 9)    # 9 features (was 8)
adj = torch.eye(1196)
well_idx = torch.randint(0, 1196, (32,))
aq_cls = ['Weathered'] * 32

output = model(wl_seq, node_f, adj, well_idx, aq_cls)
print(f"Output shape: {output.shape}")  # [32, 12]
assert output.shape == (32, 12), "Output shape incorrect"
print("✓ Model test passed")
EOF
```

---

## 7. Performance Tests

### **Database Query Performance**
```sql
-- Query should complete < 100ms
EXPLAIN ANALYZE
SELECT date, rainfall_mm
FROM rainfall
WHERE well_id = 'BPL050-OW'
AND date >= '2020-01-01'
ORDER BY date;

-- Should use index
-- Expected: Index Scan using idx_rainfall_well_date
```

### **API Load Test**
```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/v1/rainfall/BPL050-OW

# Expected results:
# - Requests per second: > 100
# - Mean response time: < 100ms
# - 99th percentile: < 500ms
```

---

## 8. Data Validation Tests

### **Correlation Analysis**
```bash
source .venv/bin/activate
python etl/analyze_rainfall_groundwater_correlation.py

# Check outputs
ls -lh data/correlation_results.csv
ls -lh data/plots/correlation_histogram.png
ls -lh data/plots/lag_distribution.png
cat data/rainfall_gw_correlation_report.md
```

**Expected Results:**
- ✅ Correlation file created
- ✅ Mean correlation: 0.3-0.7 (moderate to strong)
- ✅ Optimal lag: 1-3 months
- ✅ Plots generated

---

## 9. Regression Tests

### **Backward Compatibility**

**Test existing endpoints still work:**
```bash
# Wells endpoint
curl http://localhost:8000/api/v1/wells | jq '.[:2]'

# Forecast endpoint (should work without rainfall)
curl http://localhost:8000/api/v1/forecast/well/BPL050-OW | jq

# Stress map
curl http://localhost:8000/api/v1/stress-map/overview | jq
```

**Test model without rainfall:**
```python
# Model should work in backward-compatible mode
model = PGNN_LSTM(n_node_feat=8, use_rainfall=False)
wl_seq = torch.randn(32, 24, 1)  # Single channel
# ... forward pass should work
```

---

## 10. Acceptance Criteria

### **✅ All Tests Must Pass:**

**Data Tests:**
- [x] Rainfall extraction completes successfully
- [x] 1M+ records extracted
- [x] Seasonal patterns match climatology
- [x] No missing values or NaNs

**Database Tests:**
- [ ] Data loads to PostgreSQL without errors
- [ ] Indexes created correctly
- [ ] Queries return correct results
- [ ] Query performance < 100ms

**API Tests:**
- [ ] All 3 rainfall endpoints respond
- [ ] Response time < 500ms
- [ ] Correct data format
- [ ] Error handling works

**Frontend Tests:**
- [ ] Rainfall layer displays
- [ ] Analysis page renders
- [ ] Charts show correct data
- [ ] Responsive on all devices

**Model Tests:**
- [ ] Architecture updated correctly
- [ ] Forward pass works with rainfall input
- [ ] Backward compatible (works without rainfall)
- [ ] No gradient errors

**Integration Tests:**
- [ ] End-to-end flow works
- [ ] No console errors
- [ ] Data flows correctly from DB → API → Frontend

---

## Test Execution Summary

**Run All Tests:**
```bash
#!/bin/bash
echo "Running MP Groundwater Monitor Test Suite"
echo "=========================================="

# 1. Data Quality
echo "[1/6] Data Quality Tests..."
python -c "import pandas as pd; df = pd.read_csv('data/rainfall_well_monthly.csv'); assert len(df) > 1000000; print('✓ Data quality: PASS')"

# 2. Database (requires DB running)
echo "[2/6] Database Tests..."
# docker-compose exec db psql -U gwuser -d groundwater -c "SELECT COUNT(*) FROM rainfall;" | grep -q "1045068" && echo "✓ Database: PASS"

# 3. API (requires backend running)
echo "[3/6] API Tests..."
# curl -s http://localhost:8000/health | grep -q "healthy" && echo "✓ API health: PASS"

# 4. Frontend (requires frontend running)
echo "[4/6] Frontend Tests..."
# Manual or Cypress

# 5. Model
echo "[5/6] Model Tests..."
cd ml && python -c "from model import PGNN_LSTM; print('✓ Model import: PASS')" && cd ..

# 6. Documentation
echo "[6/6] Documentation Tests..."
test -f README.md && test -f FAQ.md && test -f RAINFALL_INTEGRATION_PLAN.md && echo "✓ Documentation: PASS"

echo ""
echo "Test Suite Complete"
```

---

## Troubleshooting

### **Common Issues:**

1. **Database connection refused**
   - Start database: `cd infra && docker-compose up -d db`
   - Wait 10 seconds for initialization

2. **Module not found (netCDF4, xarray)**
   - Install: `pip install netCDF4 xarray scipy`

3. **Frontend build errors**
   - Clear cache: `rm -rf .next`
   - Reinstall: `rm -rf node_modules && npm install`

4. **Slow API responses**
   - Check database indexes: `\d rainfall`
   - Verify connection pool settings

5. **Charts not rendering**
   - Check browser console for errors
   - Verify Recharts installed: `npm list recharts`

---

**Status**: Testing framework documented, ready for execution  
**Next**: Run tests and fix any failures  
**Owner**: Development team
