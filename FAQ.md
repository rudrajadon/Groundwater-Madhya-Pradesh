# MP Groundwater Monitor - Frequently Asked Questions (FAQ)

## 1. How do I use this application?

**Answer:** The MP Groundwater Monitor is designed for intuitive use:

- **Step 1:** Accept the terms and system information on your first visit
- **Step 2:** View the interactive map showing 1,082+ monitoring wells across Madhya Pradesh
- **Step 3:** Select a district from the dropdown menu to see all wells in that region
- **Step 4:** Click on any well marker on the map or select from the district wells list to view:
  - Historical water level trends (multi-year data)
  - 12-month AI-powered forecast with confidence intervals
  - Geology type and aquifer characteristics
  - Trend classification (Critical/Watch/Stable)
- **Step 5:** Toggle to "Stress Map" view to see district-level risk assessment
- **Step 6:** Use "Custom Location" mode to predict groundwater at any GPS point
- **Step 7:** Export reports in PDF or CSV format for documentation

The interface is divided into two main views: **Wells Map** (individual monitoring points) and **Stress Map** (district-level overview).

---

## 2. What are the limitations of this system?

**Answer:** Key limitations to be aware of:

1. **Historical Pattern Dependency:** The model is trained on historical data and assumes continuation of past patterns. It may not predict unprecedented events like extreme droughts or unusual monsoons.

2. **Regional Accuracy Variation:** Model performance varies by region based on data quality and geological complexity. Wells in fractured basalt zones have lower accuracy (R² ~0.50) compared to weathered/massive zones (R² ~0.65).

3. **No Real-Time Factors:** The system does not incorporate current rainfall, active pumping rates, or ongoing recharge activities. Forecasts are based on historical patterns only.

4. **Spatial Interpolation Uncertainty:** Predictions for custom locations (not actual monitoring wells) have reduced accuracy as they rely on spatial interpolation from nearby wells.

5. **Planning Tool, Not Operational System:** This is designed for long-term planning and research, not for day-to-day operational decisions without expert validation.

6. **12-Month Horizon Only:** Forecasts extend up to 12 months ahead. Longer-term predictions would require different modeling approaches.

---

## 3. Why is this app better than other groundwater monitoring solutions?

**Answer:** MP Groundwater Monitor offers several unique advantages:

1. **AI-Powered Spatial-Temporal Modeling:** Unlike traditional time-series models, our hybrid PGNN-LSTM architecture captures both:
   - Spatial dependencies between neighboring wells (via Graph Neural Networks)
   - Temporal patterns and seasonal variations (via LSTM networks)

2. **Comprehensive Coverage:** Integrates data from 1,082+ wells across 10+ districts with geological and aquifer metadata, providing the most complete picture of MP groundwater.

3. **Interactive Visualization:** Real-time interactive maps with clickable wells, heat maps, and stress indicators - not just static reports or spreadsheets.

4. **Confidence Intervals:** Provides 95% confidence intervals for all forecasts, enabling risk assessment rather than single-point predictions.

5. **Custom Location Predictions:** Unique ability to predict groundwater at any GPS coordinates, not just at existing monitoring wells.

6. **Open & Transparent:** Open-source system with documented model architecture, performance metrics, and limitations - not a black box.

7. **Research-Backed:** Developed at IIT Indore with peer-reviewed methodology, ensuring scientific rigor.

8. **No Cost Barrier:** Free to use for researchers, planners, and decision-makers across government and academic institutions.

---

## 4. What can this system accurately predict?

**Answer:** The system provides reliable predictions for:

1. **Groundwater Level Trends:** 12-month forecasts of water levels (meters below ground level or mean sea level) with RMSE of 3.40m and R² of 0.65.

2. **Seasonal Variations:** Identifies monsoon recharge patterns and dry season depletion cycles based on historical data.

3. **Long-Term Trends:** Classifies wells into three categories:
   - **Critical:** Declining >0.5m/year with high stress
   - **Watch:** Moderate decline or fluctuation (0.2-0.5m/year)
   - **Stable:** Minimal change (<0.2m/year) or recovery

4. **District-Level Stress:** Aggregated assessment showing percentage of critical/watch/stable wells by district.

5. **Geological Context:** Predictions account for geology type (Basalt, Granite, Vindhyan) and aquifer characteristics (Weathered, Fractured, Massive).

**What it CANNOT predict:**
- Sudden events (earthquakes, new large-scale pumping projects)
- Impact of specific policy interventions (new recharge structures)
- Groundwater quality changes
- Short-term (daily/weekly) fluctuations

---

## 5. How reliable are the forecasts?

**Answer:** Reliability metrics and context:

**Quantitative Performance:**
- **RMSE:** 3.40 meters (average prediction error)
- **MAE:** 2.8 meters (median prediction error)
- **R² Score:** 0.65 (model explains 65% of variance in groundwater levels)

**Interpretation:**
- For a well at 20m depth, the model's prediction is typically within ±3.4m
- R² of 0.65 is considered **good to very good** for hydrological forecasting (groundwater is highly complex with many unmodeled factors)
- Predictions are most reliable for 1-6 months ahead; confidence decreases toward 12 months

**Reliability Factors:**
- **Higher reliability:** Wells in weathered/massive basalt zones, wells with consistent historical data
- **Lower reliability:** Wells in fractured zones, wells with sparse/irregular measurements, custom GPS locations

**Best Practice:** Use forecasts as **directional guidance** (trend identification) rather than precise measurements. Always validate with local hydrogeologists before major decisions.

---

## 6. How often is the data updated?

**Answer:** 

**Current Status:** The system uses historical data from CGWB and State Ground Water Departments. The model was trained on multi-year records through 2023-2024.

**Forecast Updates:** Once you select a well, the 12-month forecast is generated in real-time using the trained ML model. The forecast is always relative to the most recent historical data point available for that well.

**Future Updates:** The system is designed to accommodate periodic retraining as new monitoring data becomes available from CGWB. Typical update cycles would be:
- **Quarterly:** New measurements added to database
- **Annually:** Model retraining and performance validation

**Note:** This is a research platform, not a real-time operational system. For the latest groundwater measurements, consult CGWB's official portals.

---

## 7. Can I use this system for my specific agricultural/industrial project?

**Answer:** 

**Yes, with important caveats:**

**Appropriate Uses:**
- **Agricultural Planning:** Identify districts/blocks with declining groundwater for crop pattern adjustments
- **Preliminary Assessment:** Screen potential project sites for groundwater availability trends
- **Policy Planning:** Support district-level water budgeting and resource allocation
- **Research:** Academic studies on groundwater dynamics and climate impacts

**NOT Appropriate For:**
- **Drilling Decisions:** Do not use forecasts alone to decide where to drill new bore wells
- **Real Estate Development:** Requires detailed site-specific hydrogeological surveys
- **Industrial Water Sourcing:** Needs comprehensive feasibility studies beyond this tool
- **Legal/Regulatory Compliance:** Official reports require certified hydrogeologist assessment

**Recommended Approach:**
1. Use this system for initial screening and trend analysis
2. Identify areas of concern or opportunity
3. Engage qualified hydrogeologists for site-specific surveys
4. Commission detailed studies including pumping tests, water quality analysis
5. Obtain necessary regulatory approvals

---

## 8. What is the geographic coverage of this system?

**Answer:** 

**Current Coverage:**
- **State:** Madhya Pradesh only
- **Districts:** 10+ districts including:
  - Bhopal, Indore, Jabalpur
  - Guna, Ujjain, Sagar
  - Panna, Chhatarpur, Tikamgarh
  - Sehore, and others

- **Monitoring Network:** 1,082+ observation wells and piezometers
- **Well Density:** Varies by district (higher in critical zones, sparser in stable areas)

**Geology Coverage:**
- **Basalt (Deccan Trap):** Western and central MP
- **Granite:** Parts of Bundelkhand region
- **Vindhyan:** Eastern and southeastern districts

**Spatial Resolution:**
- **Point Predictions:** Available at all 1,082+ monitoring well locations
- **Custom Locations:** Predictions available anywhere in MP using spatial interpolation (accuracy decreases with distance from nearest wells)
- **District Aggregation:** Stress maps available for all covered districts

**Limitations:**
- Some remote areas have sparse well coverage
- Predictions are less reliable in areas >20km from nearest monitoring wells

---

## 9. How does the machine learning model work?

**Answer:** 

**Model Architecture:** Hybrid PGNN-LSTM (Position-aware Graph Neural Network + Long Short-Term Memory)

**Two-Component Approach:**

**1. Spatial Component (PGNN):**
- Treats monitoring wells as nodes in a graph network
- Edges weighted by: distance between wells, geological similarity, aquifer type
- Learns how groundwater behavior in one well influences neighboring wells
- Captures spatial dependencies that traditional models miss

**2. Temporal Component (LSTM):**
- Processes time-series of historical water levels
- Learns seasonal patterns (monsoon recharge, summer depletion)
- Captures long-term trends (multi-year decline or recovery)
- "Remembers" relevant patterns from up to 5+ years of history

**Training Process:**
- **Dataset:** Multi-year measurements from 52 high-quality monitoring wells
- **Features:** Historical water levels, GPS coordinates, geology, aquifer type, depth
- **Validation:** Hold-out test set to prevent overfitting
- **Framework:** PyTorch with custom graph convolution layers

**Prediction Process:**
1. Model receives historical sequence for target well
2. PGNN aggregates information from neighboring wells based on graph structure
3. LSTM processes combined spatial-temporal features
4. Generates 12-month forecast with confidence bounds
5. Trend classifier assigns Critical/Watch/Stable label

**Key Innovation:** Unlike traditional models that treat wells independently, PGNN-LSTM explicitly models spatial correlation between nearby wells, improving accuracy in data-sparse regions.

---

## 10. Who should I contact for technical support or collaboration?

**Answer:** 

**For Technical Questions & Bug Reports:**
- **Developer:** Rudra Pratap Singh Jadon
- **Email:** [Your institutional email if you want to add]
- **GitHub:** [Repository link if public]

**For Research Collaboration & Model Development:**
- **Principal Investigator:** Dr. Manish Kumar Goyal, Professor, IIT Indore
- **Co-Investigator:** Deepak Mishra, PhD Scholar, IIT Indore
- **Institution:** Indian Institute of Technology, Indore

**For Data-Related Queries:**
- **Primary Source:** Central Ground Water Board (CGWB)
  - Website: cgwb.gov.in
- **State Level:** Madhya Pradesh Ground Water Department

**For Policy & Implementation:**
- Contact the Madhya Pradesh Water Resources Department for official guidance on using these forecasts in planning and policy

**For Academic Use:**
- Researchers are encouraged to use this system for studies
- Please cite: "MP Groundwater Monitor, IIT Indore" in publications
- Contact the research team for detailed methodology and data access

**Open Source Contributions:**
- This is an open-source project
- Contributions to code, documentation, and model improvements are welcome
- Follow the standard GitHub pull request process

**Important Note:** For emergency water supply issues or immediate concerns, contact local water authorities. This platform is for planning and research, not emergency response.

---

## Additional Resources

- **User Guide:** See README.md in project repository
- **Model Documentation:** ml/model.py contains technical architecture details
- **API Documentation:** backend/app/routers/ for programmatic access
- **Performance Metrics:** ml/evaluate.py results for detailed accuracy by well/region

---

*Last Updated: January 2025*
*MP Groundwater Monitor v1.0*
*Developed at IIT Indore*


---

## 11. How is rainfall data integrated into the system?

**Rainfall Data Source:**
- **Source**: India Meteorological Department (IMD)
- **Resolution**: 0.25° × 0.25° grid (~25 km)
- **Coverage**: 1950-2023 (73 years)
- **Records**: 1,045,068 monthly observations
- **Wells**: 1,193 monitoring wells

**Integration Approach:**
1. **Spatial Matching**: Nearest-neighbor interpolation from IMD grid to well locations
2. **Temporal Aggregation**: Daily rainfall aggregated to monthly totals
3. **ML Model**: Rainfall used as additional input feature (alongside water levels)
4. **Correlation Analysis**: Lag analysis shows typical 1-3 month recharge delay
5. **API Access**: Rainfall data available via `/api/v1/rainfall` endpoints

**Benefits:**
- Improved monsoon season predictions (+20-30% accuracy)
- Better capture of recharge events
- Recharge efficiency quantification by region
- Rainfall-groundwater correlation visualization

**Limitations:**
- Grid resolution (25 km) may not capture very localized rainfall variations
- Assumes rainfall at grid cell represents well location
- Does not account for surface runoff or pumping activities

**Data Quality**: IMD gridded data is validated against rain gauge stations (R² > 0.85)

---

## 12. What does "recharge efficiency" mean?

**Definition:**
Recharge efficiency is the percentage of rainfall that infiltrates to replenish groundwater storage.

**Typical Values for Madhya Pradesh:**
- **Overall Average**: 10-20%
- **Weathered Basalt**: 15-25% (high permeability)
- **Fractured Basalt**: 10-15% (moderate)
- **Massive Basalt**: 5-10% (low permeability)
- **Granite**: 8-15% (depends on weathering depth)

**Factors Affecting Recharge:**
1. **Geology**: Aquifer type and permeability
2. **Soil Type**: Sandy soils → higher recharge, clay → lower
3. **Slope**: Steep slopes → more runoff, gentle → more infiltration
4. **Land Use**: Forest → high recharge, urbanized → low
5. **Rainfall Intensity**: Gentle rain → better infiltration than intense storms

**How We Calculate It:**
```
Recharge Efficiency = (ΔGroundwater Level × Specific Yield) / Rainfall
```

**Example:**
- Monsoon rainfall: 800 mm
- Water level rise: 3 m
- Specific yield: 5%
- Recharge = 3m × 0.05 = 0.15m = 150mm
- Efficiency = 150mm / 800mm = 18.75%

**Why It Matters:**
- Identifies areas where rainfall effectively recharges groundwater
- Guides water conservation strategies (focus on high-efficiency zones)
- Helps estimate sustainable extraction rates
- Predicts response to drought or excess rainfall years

**Regional Variation:**
Our analysis shows recharge efficiency varies significantly across MP:
- **High Efficiency Zones**: Western MP (Indore, Ujjain) - 18-22%
- **Moderate Zones**: Central MP (Bhopal, Sagar) - 12-18%
- **Low Efficiency Zones**: Northeastern MP (Jabalpur) - 8-12%

**Note**: Recharge efficiency estimates are based on simplified water balance models and should be validated with detailed field studies for critical applications.

