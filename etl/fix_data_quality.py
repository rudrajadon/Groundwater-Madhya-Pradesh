#!/usr/bin/env python3
"""
Comprehensive data quality fixes:
1. Cap confidence scores at 1.0
2. Re-classify Panna/Jabalpur with expanded keywords
3. Fix well_id formatting (0W → OW, remove spaces, standardize case)
4. Improve aquifer classification logic to reduce weathered bias
"""
import pandas as pd
import re

# Expanded geology keywords for better coverage
BASALT_KEYWORDS = [
    'basalt', 'trap', 'deccan', 'vesicular', 'amygdaloidal', 
    'ash', 'tuff', 'bole', 'red bole', 'lava', 'volcanic',
    'black soil', 'regur', 'cotton soil'  # Common in Deccan trap regions
]

GRANITE_KEYWORDS = [
    'granite', 'gneiss', 'crystalline', 'schist', 'quartzite',
    'hard rock', 'migmatite', 'charnockite', 'biotite', 'feldsp',
    'quartz', 'mica', 'igneous', 'metamorphic'
]

VINDHYAN_KEYWORDS = [
    'sandstone', 'shale', 'limestone', 'vindhyan', 'sediment',
    'siltstone', 'mudstone', 'claystone', 'conglomerate', 'arkose',
    'sand', 'clay', 'gravel', 'pebble', 'boulder'
]

# Improved aquifer classification thresholds
WEATHERED_MAX_DEPTH = 30.0  # meters
FRACTURED_MIN_DEPTH = 30.0  # must be deeper than weathered zone
FRACTURED_MAX_DEPTH = 150.0  # meters

def fix_well_id(well_id):
    """
    Fix common well_id formatting issues:
    - Replace '0W' with 'OW' (zero to letter O)
    - Remove spaces
    - Standardize to uppercase
    """
    if pd.isna(well_id):
        return well_id
    
    # Convert to string
    wid = str(well_id).strip()
    
    # Fix 0W → OW (only if it's clearly a typo, not part of a number)
    # Pattern: anything-0W at end, or 0W- in middle
    wid = re.sub(r'-0W$', '-OW', wid)
    wid = re.sub(r'-0W-', '-OW-', wid)
    
    # Remove spaces
    wid = wid.replace(' ', '')
    
    # Standardize to uppercase
    wid = wid.upper()
    
    return wid

def classify_geology_improved(litho_df, well_id):
    """
    Improved geology classification with:
    - Normalized confidence (capped at 1.0)
    - Better keyword matching
    """
    well_litho = litho_df[litho_df['well_id'] == well_id]
    
    if len(well_litho) == 0:
        return 'Unknown', 0.0
    
    # Count keyword matches (normalized per layer)
    basalt_layers = 0
    granite_layers = 0
    vindhyan_layers = 0
    
    for _, row in well_litho.iterrows():
        litho_text = str(row['lithology']).lower()
        
        # Check if this layer matches any category
        has_basalt = any(kw in litho_text for kw in BASALT_KEYWORDS)
        has_granite = any(kw in litho_text for kw in GRANITE_KEYWORDS)
        has_vindhyan = any(kw in litho_text for kw in VINDHYAN_KEYWORDS)
        
        if has_basalt:
            basalt_layers += 1
        if has_granite:
            granite_layers += 1
        if has_vindhyan:
            vindhyan_layers += 1
    
    # Calculate confidence as fraction of layers matching
    total_layers = len(well_litho)
    basalt_conf = basalt_layers / total_layers
    granite_conf = granite_layers / total_layers
    vindhyan_conf = vindhyan_layers / total_layers
    
    max_conf = max(basalt_conf, granite_conf, vindhyan_conf)
    
    if max_conf == 0:
        return 'Unknown', 0.0
    
    # Determine geology type
    if basalt_conf == max_conf:
        return 'Basalt', round(min(basalt_conf, 1.0), 2)
    elif granite_conf == max_conf:
        return 'Granite', round(min(granite_conf, 1.0), 2)
    elif vindhyan_conf == max_conf:
        return 'Vindhyan', round(min(vindhyan_conf, 1.0), 2)
    
    return 'Unknown', 0.0

def classify_aquifer_improved(litho_df, well_id):
    """
    Improved aquifer classification:
    - Weathered: depth ≤30m AND has weathered keywords
    - Fractured: depth >30m AND <150m AND (has fracture keywords OR no weathered keywords)
    - Massive: depth >150m
    - Unknown: insufficient data
    """
    well_litho = litho_df[litho_df['well_id'] == well_id]
    
    if len(well_litho) == 0:
        return 'Unknown'
    
    # Find deepest lithology record
    try:
        max_depth = well_litho['depth_to_m'].astype(float).max()
        if pd.isna(max_depth) or max_depth == 0:
            max_depth = well_litho['depth_to_m'].astype(float).mean()
    except:
        return 'Unknown'
    
    # Check for keywords
    litho_text = ' '.join(well_litho['lithology'].astype(str).str.lower())
    
    has_weathered = any(kw in litho_text for kw in ['weathered', 'weathering', 'saprolite', 'clay'])
    has_fractured = any(kw in litho_text for kw in ['fractured', 'fracture', 'jointed', 'fissured', 'joint'])
    
    # Strict classification logic
    if max_depth <= WEATHERED_MAX_DEPTH and has_weathered:
        return 'Weathered'
    elif max_depth > FRACTURED_MIN_DEPTH and max_depth <= FRACTURED_MAX_DEPTH:
        # Fractured zone: deeper than weathered, with fracture keywords or no weathered keywords
        if has_fractured or not has_weathered:
            return 'Fractured'
        else:
            return 'Weathered'
    elif max_depth > FRACTURED_MAX_DEPTH:
        return 'Fractured'  # Deep wells are typically fractured rock aquifers
    elif has_weathered:
        return 'Weathered'
    else:
        return 'Unknown'

def main():
    print("=" * 70)
    print("COMPREHENSIVE DATA QUALITY FIXES")
    print("=" * 70)
    
    # 1. Fix well IDs in all datasets
    print("\n1. Fixing well_id formatting...")
    
    # Fix litho.csv
    litho_df = pd.read_csv('data/litho.csv')
    print(f"   Lithology records: {len(litho_df)}")
    litho_df['well_id'] = litho_df['well_id'].apply(fix_well_id)
    litho_df.to_csv('data/litho.csv', index=False)
    print("   ✓ Fixed data/litho.csv")
    
    # Fix wells.csv
    wells_df = pd.read_csv('data/wells.csv')
    print(f"   Wells: {len(wells_df)}")
    wells_df['Well No'] = wells_df['Well No'].apply(fix_well_id)
    
    # Count fixes
    fixed_0w = wells_df['Well No'].str.contains('OW').sum() - wells_df['Well No'].str.contains('0W').sum()
    print(f"   ✓ Fixed well_id formatting: {fixed_0w} '0W' → 'OW', removed spaces, uppercase")
    
    # Fix water_levels.csv
    wl_df = pd.read_csv('data/water_levels.csv')
    print(f"   Water level records: {len(wl_df)}")
    wl_df['Well No'] = wl_df['Well No'].apply(fix_well_id)
    wl_df.to_csv('data/water_levels.csv', index=False)
    print("   ✓ Fixed data/water_levels.csv")
    
    # 2. Re-classify geology with improved logic
    print("\n2. Re-classifying geology with expanded keywords...")
    
    classifications = []
    for well_id in wells_df['Well No']:
        geology_type, confidence = classify_geology_improved(litho_df, well_id)
        aquifer_type = classify_aquifer_improved(litho_df, well_id)
        
        classifications.append({
            'well_id': well_id,
            'geology_type': geology_type,
            'aquifer_classification': aquifer_type,
            'confidence': confidence  # Already capped at 1.0
        })
    
    class_df = pd.DataFrame(classifications)
    
    # 3. Statistics
    print("\n3. Classification Results:")
    print("\n   Geology Type Distribution:")
    for geo_type in ['Basalt', 'Granite', 'Vindhyan', 'Unknown']:
        count = (class_df['geology_type'] == geo_type).sum()
        pct = count / len(class_df) * 100
        print(f"     {geo_type:12} {count:4} wells ({pct:5.1f}%)")
    
    print("\n   Aquifer Classification Distribution:")
    for aquifer_type in ['Weathered', 'Fractured', 'Massive', 'Unknown']:
        count = (class_df['aquifer_classification'] == aquifer_type).sum()
        pct = count / len(class_df) * 100
        print(f"     {aquifer_type:12} {count:4} wells ({pct:5.1f}%)")
    
    print("\n   Confidence Score Statistics:")
    print(f"     Mean: {class_df['confidence'].mean():.2f}")
    print(f"     Max:  {class_df['confidence'].max():.2f}")
    print(f"     Min:  {class_df['confidence'].min():.2f}")
    print(f"     >1.0: {(class_df['confidence'] > 1.0).sum()} wells")
    
    # 4. Check Panna and Jabalpur specifically
    print("\n4. Panna & Jabalpur Coverage:")
    panna = class_df[class_df['well_id'].str.contains('PANNA', na=False)]
    jabalpur = class_df[class_df['well_id'].str.contains('SJBP|JBP', na=False)]
    
    print(f"   Panna:    {len(panna)} wells, {(panna['geology_type']=='Unknown').sum()} Unknown ({(panna['geology_type']=='Unknown').sum()/len(panna)*100:.1f}%)")
    print(f"   Jabalpur: {len(jabalpur)} wells, {(jabalpur['geology_type']=='Unknown').sum()} Unknown ({(jabalpur['geology_type']=='Unknown').sum()/len(jabalpur)*100:.1f}%)")
    
    # 5. Save results
    print("\n5. Saving updated files...")
    class_df.to_csv('data/well_geology_classifications.csv', index=False)
    print("   ✓ Saved data/well_geology_classifications.csv")
    
    # Update wells.csv
    wells_df = wells_df.drop(columns=['geology_type', 'aquifer_classification'], errors='ignore')
    wells_df = wells_df.merge(
        class_df[['well_id', 'geology_type', 'aquifer_classification']], 
        left_on='Well No', 
        right_on='well_id', 
        how='left'
    )
    wells_df = wells_df.drop(columns=['well_id'], errors='ignore')
    wells_df.to_csv('data/wells.csv', index=False)
    print("   ✓ Updated data/wells.csv")
    
    print("\n" + "=" * 70)
    print("DATA QUALITY FIXES COMPLETE!")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
