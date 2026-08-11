# Aquifer Zone / Rock Type Data

## Current Status
- **Map popups** now show: `Well ID` + `Block` (+ `Aquifer Zone` if available)
- **Trend labels** (Critical/Watch/Stable) removed from popups
- **Database schema** supports aquifer zone data but currently unpopulated

## Database Schema

The `wells` table has these columns for rock/aquifer type:
- `aquifer_zone` (text): Main aquifer classification (e.g., "Weathered", "Fractured", "Massive")
- `wthr_pct` (numeric): Percentage of weathered rock
- `frac_pct` (numeric): Percentage of fractured rock  
- `mass_pct` (numeric): Percentage of massive rock

## How to Populate Data

### Option 1: Update from CSV
If you have aquifer zone data in a CSV file:

```sql
-- Example: Update from a CSV with columns: well_id, aquifer_zone
COPY temp_aquifer (well_id, aquifer_zone) 
FROM '/path/to/aquifer_data.csv' 
CSV HEADER;

UPDATE wells w
SET aquifer_zone = t.aquifer_zone
FROM temp_aquifer t
WHERE w.well_id = t.well_id;

DROP TABLE temp_aquifer;
```

### Option 2: Update Specific Wells
```sql
-- Update individual wells
UPDATE wells 
SET aquifer_zone = 'Weathered Granite'
WHERE well_id = 'TKM030-OW';

-- Batch update by district
UPDATE wells 
SET aquifer_zone = 'Fractured Basalt'
WHERE district = 'Indore';
```

### Option 3: Calculate from Lithology Percentages
If you have percentage data:

```sql
-- Set aquifer zone based on dominant rock type
UPDATE wells
SET aquifer_zone = CASE 
    WHEN wthr_pct > frac_pct AND wthr_pct > mass_pct THEN 'Weathered'
    WHEN frac_pct > mass_pct THEN 'Fractured'
    ELSE 'Massive'
END
WHERE wthr_pct IS NOT NULL 
  AND frac_pct IS NOT NULL 
  AND mass_pct IS NOT NULL;
```

### Option 4: Use Lithology Logs
Process the lithology logs CSV:

```python
import pandas as pd
import psycopg2

# Read lithology data
litho = pd.read_csv('data/litho.csv')

# Group by well and determine dominant lithology
dominant_litho = litho.groupby('Well_No')['Lithology'].agg(
    lambda x: x.value_counts().index[0] if len(x) > 0 else None
)

# Update database
conn = psycopg2.connect(
    host="localhost", port=5432,
    database="groundwater", user="gwuser", password="changeme"
)
cur = conn.cursor()

for well_id, lithology in dominant_litho.items():
    cur.execute("""
        UPDATE wells 
        SET aquifer_zone = %s 
        WHERE well_id = %s
    """, (lithology, well_id))

conn.commit()
conn.close()
```

## Example Aquifer Zone Classifications

Common classifications for Madhya Pradesh:

### By Rock Type
- **Weathered Granite**: Shallow aquifer, good yield
- **Fractured Basalt**: Moderate to good yield
- **Alluvial**: High yield, confined aquifer
- **Crystalline**: Poor yield, limited storage

### By Weathering
- **Weathered**: 0-15m depth, high permeability
- **Fractured**: 15-50m depth, moderate permeability
- **Massive**: >50m depth, low permeability

### By Hydrogeology
- **Phreatic**: Unconfined aquifer
- **Semi-confined**: Leaky aquifer
- **Confined**: Artesian aquifer

## Current Display Behavior

**Map Popup (after update):**
```
TKM030-OW
Palera
[Aquifer Zone if available]
```

**Before:**
```
TKM030-OW
Palera - Stable
```

The trend classification (Critical/Watch/Stable) is still used for:
- Map marker **border colors** (red/amber/green)
- Detailed forecast view when clicking a well
- Backend classification logic

## Recommended Next Steps

1. **Source Data**: Identify source for aquifer zone classifications
   - Geological Survey of India (GSI) reports
   - Central Ground Water Board (CGWB) data
   - State Water Resource Department
   - Existing well completion reports

2. **Classify Wells**: Apply dominant aquifer type to each well
   - Use lithology logs if available
   - Use district/block geology maps
   - Use depth and yield characteristics

3. **Update Database**: Run SQL updates to populate `aquifer_zone`

4. **Validate**: Check a few wells to ensure data is accurate
   ```sql
   SELECT well_id, block, aquifer_zone, trend_label 
   FROM wells 
   WHERE aquifer_zone IS NOT NULL 
   LIMIT 10;
   ```

5. **Restart Frontend**: Changes appear immediately (no rebuild needed)
   ```bash
   docker compose -f infra/docker-compose.yml restart frontend
   ```

## Data Sources

### For Madhya Pradesh Aquifer Data:
- **CGWB Reports**: http://cgwb.gov.in/
- **MPGWB**: Madhya Pradesh Ground Water Board
- **District Hydrogeology Maps**: Available from GSI

### Example Data Format:
```csv
well_id,aquifer_zone,wthr_pct,frac_pct,mass_pct
TKM030-OW,Weathered Granite,60,30,10
SIND-011-PZ,Fractured Basalt,20,70,10
BPL023-OW,Alluvial,80,15,5
```

## Notes

- Empty `aquifer_zone` = popup shows only block name
- With `aquifer_zone` = popup shows block + aquifer type
- This makes the map more informative for hydrogeologists
- Trend classification still visible via marker colors and detailed view
