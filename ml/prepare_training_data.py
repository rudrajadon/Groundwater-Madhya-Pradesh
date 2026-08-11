#!/usr/bin/env python3
"""
Prepare training data for PGNN-LSTM model.
Combines water levels, rainfall features, geology, and well metadata.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import pickle


def load_and_prepare_data():
    """
    Load all data sources and prepare for training.
    
    Returns:
        combined_df: DataFrame with all features per well-month
        wells_df: Well metadata
    """
    print("=" * 70)
    print("Preparing Training Data for PGNN-LSTM")
    print("=" * 70)
    
    # 1. Load water levels
    print("\n1. Loading water level data...")
    water_levels = pd.read_csv('data/water_levels.csv')
    water_levels['date'] = pd.to_datetime(water_levels['date'], format='mixed')
    water_levels = water_levels.rename(columns={'Well No': 'well_id', 'Water Level': 'depth_bgl_m'})
    water_levels = water_levels.sort_values(['well_id', 'date'])
    
    print(f"   Water level records: {len(water_levels):,}")
    print(f"   Wells: {water_levels['well_id'].nunique()}")
    print(f"   Date range: {water_levels['date'].min()} to {water_levels['date'].max()}")
    
    # 2. Load rainfall features
    print("\n2. Loading rainfall features...")
    rainfall_features = pd.read_csv('data/rainfall_features.csv')
    rainfall_features['date'] = pd.to_datetime(rainfall_features['date'])
    rainfall_features = rainfall_features.rename(columns={'well_id': 'well_id'})
    
    print(f"   Rainfall feature records: {len(rainfall_features):,}")
    print(f"   Wells with rainfall data: {rainfall_features['well_id'].nunique()}")
    
    # 3. Load wells metadata
    print("\n3. Loading well metadata...")
    wells_df = pd.read_csv('data/wells.csv')
    print(f"   Wells in database: {len(wells_df)}")
    
    # 4. Merge water levels with rainfall features
    print("\n4. Merging water levels with rainfall features...")
    combined = water_levels.merge(
        rainfall_features,
        on=['well_id', 'date'],
        how='left'
    )
    
    print(f"   Combined records: {len(combined):,}")
    print(f"   Records with rainfall data: {combined['rain_current'].notna().sum():,}")
    
    # 5. Add well metadata
    print("\n5. Adding well metadata...")
    combined = combined.merge(
        wells_df[['Well No', 'District', 'Block / Mandal', 'geology_type', 
                  'aquifer_classification', 'Elevation of Ground Level',
                  'Northing', 'Easting']],
        left_on='well_id',
        right_on='Well No',
        how='left'
    )
    
    # 6. Fill missing rainfall with 0 (pre-1976 data)
    rain_cols = ['rain_current', 'rain_lag1', 'rain_lag2', 'rain_lag3',
                 'rain_cum_3m', 'rain_cum_6m', 'rain_annual_avg']
    for col in rain_cols:
        if col in combined.columns:
            combined[col] = combined[col].fillna(0)
    
    # 7. Remove records with missing critical data
    print("\n6. Filtering valid records...")
    initial_count = len(combined)
    
    combined = combined[
        combined['depth_bgl_m'].notna() &
        combined['geology_type'].notna() &
        combined['Northing'].notna()
    ]
    
    print(f"   Kept {len(combined):,} / {initial_count:,} records")
    print(f"   Removed {initial_count - len(combined):,} records with missing data")
    
    # 8. Summary statistics
    print("\n7. Data Summary:")
    print(f"   Final dataset size: {len(combined):,} records")
    print(f"   Wells: {combined['well_id'].nunique()}")
    print(f"   Date range: {combined['date'].min()} to {combined['date'].max()}")
    print(f"   Water level range: {combined['depth_bgl_m'].min():.2f} - {combined['depth_bgl_m'].max():.2f} m BGL")
    
    print(f"\n   Geology distribution:")
    for geology, count in combined['geology_type'].value_counts().items():
        pct = 100 * count / len(combined)
        print(f"     {geology:12} {count:7,} records ({pct:5.1f}%)")
    
    print(f"\n   District distribution:")
    for district, count in combined['District'].value_counts().head(5).items():
        print(f"     {district:20} {count:6,} records")
    
    # 9. Save prepared data
    output_path = 'data/training_data_prepared.csv'
    combined.to_csv(output_path, index=False)
    print(f"\n✓ Prepared data saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("✓ Data preparation complete")
    print("=" * 70)
    
    return combined, wells_df


def create_time_series_sequences(combined_df, seq_len=24, horizon=12, train_test_split_year=2019):
    """
    Create training and test sequences for PGNN-LSTM.
    
    Args:
        combined_df: DataFrame with all features
        seq_len: Lookback window (months)
        horizon: Forecast horizon (months)
        train_test_split_year: Year to split train/test
    
    Returns:
        train_sequences: List of training examples
        test_sequences: List of test examples
    """
    print("\nCreating time series sequences...")
    print(f"  Sequence length: {seq_len} months")
    print(f"  Forecast horizon: {horizon} months")
    print(f"  Train/test split: ≤{train_test_split_year} / >{train_test_split_year}")
    
    train_sequences = []
    test_sequences = []
    
    wells = combined_df['well_id'].unique()
    
    for well_id in wells:
        well_data = combined_df[combined_df['well_id'] == well_id].sort_values('date')
        
        # Need at least seq_len + horizon records
        if len(well_data) < seq_len + horizon:
            continue
        
        # Extract features
        dates = well_data['date'].values
        water_levels = well_data['depth_bgl_m'].values
        
        # Rainfall features (if available)
        rain_features = well_data[[
            'rain_current', 'rain_lag1', 'rain_lag2', 'rain_lag3',
            'rain_cum_3m', 'rain_cum_6m', 'rain_annual_avg'
        ]].values if 'rain_current' in well_data.columns else None
        
        # Well metadata
        geology_type = well_data['geology_type'].iloc[0]
        aquifer_class = well_data['aquifer_classification'].iloc[0]
        district = well_data['District'].iloc[0]
        
        # Create sequences
        for i in range(len(water_levels) - seq_len - horizon + 1):
            # Input sequence
            input_wl = water_levels[i:i + seq_len]
            input_rain = rain_features[i:i + seq_len] if rain_features is not None else None
            
            # Target sequence
            target_wl = water_levels[i + seq_len:i + seq_len + horizon]
            
            # Date of forecast
            forecast_date = dates[i + seq_len]
            forecast_year = pd.Timestamp(forecast_date).year
            
            sequence = {
                'well_id': well_id,
                'date': forecast_date,
                'input_wl': input_wl,
                'input_rain': input_rain,
                'target_wl': target_wl,
                'geology_type': geology_type,
                'aquifer_class': aquifer_class,
                'district': district
            }
            
            # Split train/test by year
            if forecast_year <= train_test_split_year:
                train_sequences.append(sequence)
            else:
                test_sequences.append(sequence)
    
    print(f"\n  Training sequences: {len(train_sequences):,}")
    print(f"  Test sequences: {len(test_sequences):,}")
    print(f"  Wells in training: {len(set(s['well_id'] for s in train_sequences))}")
    print(f"  Wells in testing: {len(set(s['well_id'] for s in test_sequences))}")
    
    return train_sequences, test_sequences


def save_sequences(train_sequences, test_sequences, output_dir='data'):
    """Save sequences to pickle files for training."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    train_path = f'{output_dir}/train_sequences.pkl'
    test_path = f'{output_dir}/test_sequences.pkl'
    
    with open(train_path, 'wb') as f:
        pickle.dump(train_sequences, f)
    
    with open(test_path, 'wb') as f:
        pickle.dump(test_sequences, f)
    
    print(f"\n✓ Sequences saved:")
    print(f"  Training: {train_path}")
    print(f"  Testing: {test_path}")


def main():
    # Prepare data
    combined_df, wells_df = load_and_prepare_data()
    
    # Create sequences
    train_sequences, test_sequences = create_time_series_sequences(
        combined_df,
        seq_len=24,
        horizon=12,
        train_test_split_year=2019
    )
    
    # Save sequences
    save_sequences(train_sequences, test_sequences)
    
    print("\n" + "=" * 70)
    print("✓ Training data preparation complete!")
    print("  Next: Run ml/train_pgnn_lstm.py to train the model")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
