#!/usr/bin/env python3
"""
Create 7 rainfall features for each well as required by PGNN-LSTM model.
Features: current month, lag-1, lag-2, lag-3, cumulative 3-month, 6-month, annual average
Uses IDW (Inverse Distance Weighting) to interpolate from rainfall stations to wells.
"""
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

def idw_interpolation(target_lat, target_lon, stations_df, n_neighbors=3, power=2):
    """
    Interpolate rainfall using Inverse Distance Weighting (IDW).
    Returns: rainfall value for target location
    """
    # Calculate distances from target to all stations
    target_point = np.array([[target_lat, target_lon]])
    station_points = stations_df[['lat', 'lon']].values
    
    distances = cdist(target_point, station_points, metric='euclidean')[0]
    
    # Get nearest neighbors
    nearest_indices = np.argsort(distances)[:n_neighbors]
    nearest_distances = distances[nearest_indices]
    nearest_rainfall = stations_df.iloc[nearest_indices]['rainfall_mm'].values
    
    # Avoid division by zero for exact matches
    nearest_distances = np.where(nearest_distances == 0, 1e-10, nearest_distances)
    
    # Calculate IDW weights
    weights = 1 / (nearest_distances ** power)
    weights = weights / weights.sum()
    
    # Weighted average
    interpolated_rain = np.sum(weights * nearest_rainfall)
    
    return interpolated_rain

def create_rainfall_features_for_well(well_id, well_lat, well_lon, rainfall_stations_df):
    """
    Create 7 rainfall features for a single well.
    Returns: DataFrame with date and 7 features
    """
    # Get all unique dates
    dates = rainfall_stations_df['date'].unique()
    dates = sorted(pd.to_datetime(dates))
    
    # Interpolate rainfall for this well at each date
    well_rainfall = []
    for date in dates:
        date_data = rainfall_stations_df[rainfall_stations_df['date'] == date]
        interpolated = idw_interpolation(well_lat, well_lon, date_data, n_neighbors=3)
        well_rainfall.append({'date': date, 'rainfall_mm': interpolated})
    
    well_rain_df = pd.DataFrame(well_rainfall)
    
    # Create 7 features
    features = []
    for idx in range(len(well_rain_df)):
        date = well_rain_df.iloc[idx]['date']
        
        # Feature 1: Current month rainfall
        current = well_rain_df.iloc[idx]['rainfall_mm']
        
        # Feature 2-4: Lag-1, Lag-2, Lag-3
        lag1 = well_rain_df.iloc[idx-1]['rainfall_mm'] if idx >= 1 else 0
        lag2 = well_rain_df.iloc[idx-2]['rainfall_mm'] if idx >= 2 else 0
        lag3 = well_rain_df.iloc[idx-3]['rainfall_mm'] if idx >= 3 else 0
        
        # Feature 5: Cumulative 3-month
        cum_3m = well_rain_df.iloc[max(0, idx-2):idx+1]['rainfall_mm'].sum()
        
        # Feature 6: Cumulative 6-month
        cum_6m = well_rain_df.iloc[max(0, idx-5):idx+1]['rainfall_mm'].sum()
        
        # Feature 7: Annual average (rolling 12-month)
        if idx >= 11:
            annual_avg = well_rain_df.iloc[idx-11:idx+1]['rainfall_mm'].mean()
        else:
            annual_avg = well_rain_df.iloc[:idx+1]['rainfall_mm'].mean()
        
        features.append({
            'well_id': well_id,
            'date': date,
            'rain_current': round(current, 1),
            'rain_lag1': round(lag1, 1),
            'rain_lag2': round(lag2, 1),
            'rain_lag3': round(lag3, 1),
            'rain_cum_3m': round(cum_3m, 1),
            'rain_cum_6m': round(cum_6m, 1),
            'rain_annual_avg': round(annual_avg, 1)
        })
    
    return pd.DataFrame(features)

def main():
    """Create rainfall features for all wells."""
    print("=" * 70)
    print("Creating Rainfall Features for PGNN-LSTM Model")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading data...")
    rainfall_stations = pd.read_csv('data/rainfall_stations.csv')
    rainfall_stations['date'] = pd.to_datetime(rainfall_stations['date'])
    wells_df = pd.read_csv('data/wells.csv')
    
    print(f"   Rainfall stations: {rainfall_stations['well_id'].nunique()}")
    print(f"   Wells: {len(wells_df)}")
    
    # Filter wells with valid coordinates
    valid_wells = wells_df[
        wells_df['Northing'].notna() & 
        wells_df['Easting'].notna()
    ].copy()
    print(f"   Wells with coordinates: {len(valid_wells)}")
    
    # Create features for each well
    print("\n2. Creating rainfall features using IDW interpolation...")
    all_features = []
    
    # Process in batches for progress display
    batch_size = 100
    for batch_start in range(0, len(valid_wells), batch_size):
        batch_end = min(batch_start + batch_size, len(valid_wells))
        batch = valid_wells.iloc[batch_start:batch_end]
        
        print(f"   Processing wells {batch_start+1}-{batch_end}/{len(valid_wells)}...")
        
        for _, well in batch.iterrows():
            well_id = well['Well No']
            lat = float(well['Northing'])
            lon = float(well['Easting'])
            
            features_df = create_rainfall_features_for_well(
                well_id, lat, lon, rainfall_stations
            )
            all_features.append(features_df)
    
    # Combine all features
    print("\n3. Combining features...")
    all_features_df = pd.concat(all_features, ignore_index=True)
    
    # Save to CSV
    output_file = 'data/rainfall_features.csv'
    all_features_df.to_csv(output_file, index=False)
    print(f"   ✓ Saved {len(all_features_df):,} records to: {output_file}")
    
    # Statistics
    print("\n4. Feature Statistics:")
    print(f"   Wells with features: {all_features_df['well_id'].nunique()}")
    print(f"   Date range: {all_features_df['date'].min()} to {all_features_df['date'].max()}")
    print(f"   Total records: {len(all_features_df):,}")
    
    print("\n   Feature ranges:")
    for col in ['rain_current', 'rain_lag1', 'rain_lag2', 'rain_lag3', 
                'rain_cum_3m', 'rain_cum_6m', 'rain_annual_avg']:
        mean_val = all_features_df[col].mean()
        max_val = all_features_df[col].max()
        print(f"     {col:20} mean={mean_val:6.1f} mm, max={max_val:6.1f} mm")
    
    # Sample output
    print("\n5. Sample Features:")
    sample = all_features_df[all_features_df['well_id'] == all_features_df['well_id'].iloc[0]].head(5)
    print(sample.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("✓ Rainfall feature engineering complete!")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
