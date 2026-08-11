#!/usr/bin/env python3
"""
Classify wells by geology type based on lithology data.
Categories: Basalt (Deccan Trap), Granite (Hard rock), Vindhyan (Sedimentary)
Also classify aquifer type: Weathered, Fractured, Massive based on depth.
"""
import pandas as pd
import re
from collections import Counter

# Geology classification keywords (from PGNN notebook logic)
BASALT_KEYWORDS = [
    'basalt', 'trap', 'deccan', 'vesicular', 'amygdaloidal', 
    'ash', 'tuff', 'bole', 'red bole', 'lava'
]

GRANITE_KEYWORDS = [
    'granite', 'gneiss', 'crystalline', 'schist', 'quartzite',
    'hard rock', 'migmatite', 'charnockite', 'biotite'
]

VINDHYAN_KEYWORDS = [
    'sandstone', 'shale', 'limestone', 'vindhyan', 'sediment',
    'siltstone', 'mudstone', 'claystone', 'conglomerate', 'arkose'
]

# Aquifer classification by depth (Singhal & Gupta, 2010)
WEATHERED_MAX_DEPTH = 30.0  # meters
FRACTURED_MAX_DEPTH = 100.0  # meters

def classify_geology_from_lithology(litho_df, well_id):
    """
    Classify a well's geology type based on its lithology records.
    Returns: ('Basalt'|'Granite'|'Vindhyan'|'Unknown', confidence_score)
    """
    well_litho = litho_df[litho_df['well_id'] == well_id]
    
    if len(well_litho) == 0:
        return 'Unknown', 0.0
    
    # Count keyword matches across all lithology descriptions
    basalt_score = 0
    granite_score = 0
    vindhyan_score = 0
    
    for _, row in well_litho.iterrows():
        litho_text = str(row['lithology']).lower()
        
        # Check each keyword
        for keyword in BASALT_KEYWORDS:
            if keyword in litho_text:
                basalt_score += 1
        
        for keyword in GRANITE_KEYWORDS:
            if keyword in litho_text:
                granite_score += 1
        
        for keyword in VINDHYAN_KEYWORDS:
            if keyword in litho_text:
                vindhyan_score += 1
    
    # Determine geology type
    max_score = max(basalt_score, granite_score, vindhyan_score)
    
    if max_score == 0:
        return 'Unknown', 0.0
    
    if basalt_score == max_score:
        return 'Basalt', basalt_score / len(well_litho)
    elif granite_score == max_score:
        return 'Granite', granite_score / len(well_litho)
    elif vindhyan_score == max_score:
        return 'Vindhyan', vindhyan_score / len(well_litho)
    
    return 'Unknown', 0.0

def classify_aquifer_type(litho_df, well_id):
    """
    Classify aquifer type based on depth and lithology keywords.
    Returns: 'Weathered' | 'Fractured' | 'Massive' | 'Unknown'
    """
    well_litho = litho_df[litho_df['well_id'] == well_id]
    
    if len(well_litho) == 0:
        return 'Unknown'
    
    # Find deepest lithology record
    try:
        max_depth = well_litho['depth_to_m'].astype(float).max()
    except:
        max_depth = 0
    
    # Check for weathered/fractured keywords in lithology
    litho_text = ' '.join(well_litho['lithology'].astype(str).str.lower())
    
    has_weathered = any(kw in litho_text for kw in ['weathered', 'weathering', 'saprolite'])
    has_fractured = any(kw in litho_text for kw in ['fractured', 'fracture', 'jointed', 'fissured'])
    
    # Classification logic (Singhal & Gupta, 2010)
    if max_depth <= WEATHERED_MAX_DEPTH or has_weathered:
        return 'Weathered'
    elif max_depth <= FRACTURED_MAX_DEPTH or has_fractured:
        return 'Fractured'
    else:
        return 'Massive'

def main():
    """Main classification process."""
    print("=" * 60)
    print("Classifying Wells by Geology Type")
    print("=" * 60)
    
    # Load data
    print("\n1. Loading data...")
    litho_df = pd.read_csv('data/litho.csv')
    wells_df = pd.read_csv('data/wells.csv')
    
    print(f"   Lithology records: {len(litho_df)}")
    print(f"   Wells: {len(wells_df)}")
    
    # Get unique well IDs from lithology data
    well_ids_with_litho = set(litho_df['well_id'].unique())
    print(f"   Wells with lithology data: {len(well_ids_with_litho)}")
    
    # Classify each well
    print("\n2. Classifying wells...")
    classifications = []
    
    for well_id in wells_df['Well No']:
        geology_type, confidence = classify_geology_from_lithology(litho_df, well_id)
        aquifer_type = classify_aquifer_type(litho_df, well_id)
        
        classifications.append({
            'well_id': well_id,
            'geology_type': geology_type,
            'aquifer_classification': aquifer_type,
            'confidence': round(confidence, 2)
        })
    
    # Create classifications dataframe
    class_df = pd.DataFrame(classifications)
    
    # Statistics
    print("\n3. Classification Results:")
    print("\n   Geology Type Distribution:")
    for geo_type, count in class_df['geology_type'].value_counts().items():
        pct = count / len(class_df) * 100
        print(f"     {geo_type:12} {count:4} wells ({pct:5.1f}%)")
    
    print("\n   Aquifer Classification Distribution:")
    for aquifer_type, count in class_df['aquifer_classification'].value_counts().items():
        pct = count / len(class_df) * 100
        print(f"     {aquifer_type:12} {count:4} wells ({pct:5.1f}%)")
    
    # Save classifications
    output_file = 'data/well_geology_classifications.csv'
    class_df.to_csv(output_file, index=False)
    print(f"\n✓ Saved classifications to: {output_file}")
    
    # Show samples for each geology type
    print("\n4. Sample Wells by Geology Type:")
    for geo_type in ['Basalt', 'Granite', 'Vindhyan']:
        samples = class_df[class_df['geology_type'] == geo_type].head(3)
        if len(samples) > 0:
            print(f"\n   {geo_type}:")
            for _, row in samples.iterrows():
                print(f"     - {row['well_id']} ({row['aquifer_classification']}, conf={row['confidence']})")
    
    # Merge with wells.csv
    print("\n5. Updating wells.csv with geology classifications...")
    wells_df = wells_df.merge(
        class_df[['well_id', 'geology_type', 'aquifer_classification']], 
        left_on='Well No', 
        right_on='well_id', 
        how='left'
    )
    
    # Drop duplicate well_id column
    if 'well_id' in wells_df.columns:
        wells_df = wells_df.drop('well_id', axis=1)
    
    # Save updated wells.csv
    wells_df.to_csv('data/wells.csv', index=False)
    print(f"✓ Updated data/wells.csv with geology_type and aquifer_classification columns")
    
    print("\n" + "=" * 60)
    print("Classification Complete!")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
