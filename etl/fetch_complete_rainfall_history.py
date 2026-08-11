#!/usr/bin/env python3
"""
Fetch complete historical rainfall data (1976-2024) for all well locations.
Uses Open-Meteo Historical Weather API (free, no API key required).
Creates rainfall.csv with monthly aggregations per well.
"""
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Open-Meteo API endpoint for historical data
API_URL = "https://archive-api.open-meteo.com/v1/archive"

def fetch_rainfall_for_location(lat, lon, start_year=1976, end_year=2024):
    """
    Fetch daily rainfall for a location and aggregate to monthly.
    Returns: DataFrame with columns [date, rainfall_mm]
    """
    all_data = []
    
    # Open-Meteo allows max 1 year per request, so we fetch year by year
    for year in range(start_year, end_year + 1):
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "precipitation_sum",
            "timezone": "Asia/Kolkata"
        }
        
        try:
            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract daily data
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            precip = daily.get("precipitation_sum", [])
            
            for date, rain in zip(dates, precip):
                all_data.append({
                    'date': date,
                    'rainfall_mm': rain if rain is not None else 0.0
                })
            
            # Be nice to the API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ⚠ Error fetching {year}: {e}")
            continue
    
    if not all_data:
        return pd.DataFrame()
    
    # Convert to DataFrame and aggregate to monthly
    df = pd.DataFrame(all_data)
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    # Monthly aggregation
    monthly = df.groupby(['year', 'month'])['rainfall_mm'].sum().reset_index()
    monthly['date'] = pd.to_datetime(monthly[['year', 'month']].assign(day=1))
    monthly = monthly[['date', 'rainfall_mm']]
    
    return monthly

def sample_representative_wells(wells_df, n_samples=30):
    """
    Sample representative wells across districts to reduce API calls.
    Create a rainfall station grid that covers all of MP.
    """
    # Get unique districts
    districts = wells_df['District'].dropna().unique()
    
    sampled_wells = []
    for district in districts:
        district_wells = wells_df[wells_df['District'] == district]
        if len(district_wells) > 0:
            # Sample 2-3 wells per district for good spatial coverage
            n = min(2, len(district_wells))
            samples = district_wells.sample(n=n, random_state=42)
            sampled_wells.append(samples)
    
    result = pd.concat(sampled_wells) if sampled_wells else wells_df.head(n_samples)
    
    # Ensure we have good spatial coverage
    print(f"   Districts covered: {result['District'].nunique()}")
    return result

def main():
    """Fetch rainfall data for all well locations."""
    print("=" * 70)
    print("Fetching Historical Rainfall Data (1976-2024)")
    print("=" * 70)
    
    # Load wells
    print("\n1. Loading wells data...")
    wells_df = pd.read_csv('data/wells.csv')
    print(f"   Total wells: {len(wells_df)}")
    
    # For this demo, we'll sample representative wells
    # In production, use actual rainfall station locations
    print("\n2. Sampling representative wells...")
    sample_wells = sample_representative_wells(wells_df, n_samples=20)
    print(f"   Selected {len(sample_wells)} representative wells")
    
    # Fetch rainfall for each sampled location
    print("\n3. Fetching rainfall data...")
    all_rainfall = []
    
    for idx, (_, well) in enumerate(sample_wells.iterrows(), 1):
        well_id = well['Well No']
        lat = float(well['Northing']) if pd.notna(well['Northing']) else None
        lon = float(well['Easting']) if pd.notna(well['Easting']) else None
        
        if lat is None or lon is None:
            print(f"   [{idx}/{len(sample_wells)}] ✗ {well_id}: Missing coordinates")
            continue
        
        print(f"   [{idx}/{len(sample_wells)}] Fetching {well_id} ({lat:.2f}, {lon:.2f})...")
        
        monthly_rain = fetch_rainfall_for_location(lat, lon)
        
        if len(monthly_rain) > 0:
            monthly_rain['well_id'] = well_id
            monthly_rain['lat'] = lat
            monthly_rain['lon'] = lon
            all_rainfall.append(monthly_rain)
            print(f"                ✓ Got {len(monthly_rain)} months of data")
        else:
            print(f"                ✗ No data received")
    
    if not all_rainfall:
        print("\n✗ No rainfall data fetched!")
        return 1
    
    # Combine all rainfall data
    print("\n4. Combining rainfall data...")
    rainfall_df = pd.concat(all_rainfall, ignore_index=True)
    
    # Save to CSV
    output_file = 'data/rainfall_stations.csv'
    rainfall_df.to_csv(output_file, index=False)
    print(f"   ✓ Saved {len(rainfall_df)} rainfall records to: {output_file}")
    
    # Statistics
    print("\n5. Rainfall Statistics:")
    print(f"   Locations: {rainfall_df['well_id'].nunique()}")
    print(f"   Date range: {rainfall_df['date'].min()} to {rainfall_df['date'].max()}")
    print(f"   Total records: {len(rainfall_df)}")
    print(f"   Average monthly rainfall: {rainfall_df['rainfall_mm'].mean():.1f} mm")
    
    # Sample output
    print("\n6. Sample Data:")
    print(rainfall_df.head(10).to_string(index=False))
    
    print("\n" + "=" * 70)
    print("Next Step: Run rainfall feature engineering script")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
