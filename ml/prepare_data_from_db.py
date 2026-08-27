#!/usr/bin/env python3
"""
Prepare data for PGNN-LSTM training directly from PostgreSQL database.
Uses relaxed criteria to include more wells.
"""
import os
import sys
import pandas as pd
import numpy as np
import pickle
import torch
from sklearn.preprocessing import MinMaxScaler
import psycopg2

# Add ml directory to path
sys.path.insert(0, os.path.dirname(__file__))
from preprocessing import classify_aquifer, build_graph, build_node_features

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'groundwater',
    'user': 'gwuser',
    'password': 'changeme'
}

def main():
    print("="*70)
    print("PREPARING DATA FOR PGNN-LSTM (FROM DATABASE - RELAXED CRITERIA)")
    print("="*70)
    
    # Connect to database
    print("\n[1/7] Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Load water levels
    print("\n[2/7] Loading water level data...")
    wl = pd.read_sql("""
        SELECT r.well_id, r.date, r.head_msl_m
        FROM readings r
        WHERE r.head_msl_m IS NOT NULL
        ORDER BY r.well_id, r.date
    """, conn)
    print(f"  Records: {len(wl):,}")
    print(f"  Wells: {wl['well_id'].nunique()}")
    print(f"  Range: {wl['head_msl_m'].min():.1f} - {wl['head_msl_m'].max():.1f} m MSL")
    
    # Load well metadata
    print("\n[3/7] Loading well metadata...")
    wells = pd.read_sql("""
        SELECT well_id as "Well No",
               ST_Y(geom::geometry) as latitude,
               ST_X(geom::geometry) as longitude,
               ST_Y(geom::geometry) as "Northing",
               ST_X(geom::geometry) as "Easting",
               elevation_m as "Elevation of Ground Level",
               district as "District",
               block as "Block / Mandal",
               geology_type,
               aquifer_classification,
               aquifer_zone
        FROM wells
        WHERE geom IS NOT NULL
    """, conn)
    # Add missing columns expected by preprocessing
    wells["Command Area"] = 0.0  # Not available in database
    print(f"  Wells with coordinates: {len(wells)}")
    
    # Load lithology from CSV (table structure is different)
    print("\n[4/7] Loading lithology data...")
    try:
        litho = pd.read_csv('data/litho.csv')
        # Rename to match preprocessing.py expectations
        litho = litho.rename(columns={
            'well_id': 'Well_No',
            'depth_to_m': 'Depth_To',
            'lithology': 'Lithology'
        })
        print(f"  Lithology records: {len(litho)}")
    except Exception as e:
        print(f"  Warning: Could not load lithology CSV: {e}")
        litho = pd.DataFrame()  # Empty dataframe
    
    conn.close()
    
    # Build monthly series with VERY RELAXED criteria
    print("\n[5/7] Building monthly time series (VERY RELAXED)...")
    print("  Criteria:")
    print("    - Minimum months: 30 (2.5 years) [was 36]")
    print("    - Interpolation limit: 6 months [was 3]")
    
    wl['date'] = pd.to_datetime(wl['date'])
    monthly = {}
    excluded = []
    
    for well_id in wl['well_id'].unique():
        wdf = wl[wl['well_id'] == well_id].set_index('date')
        ms = wdf['head_msl_m'].resample('MS').mean()
        
        # More lenient interpolation
        ms = ms.interpolate(method='linear', limit=6).dropna()
        
        if len(ms) >= 30:  # 2.5 years minimum (lowered from 36)
            monthly[well_id] = ms
        else:
            excluded.append((well_id, len(ms)))
    
    well_list = sorted(monthly.keys())
    print(f"  ✓ Included: {len(well_list)} wells")
    print(f"  ✗ Excluded: {len(excluded)} wells (insufficient continuous data)")
    
    if len(excluded) > 0:
        print(f"\n  Top 10 excluded wells:")
        for well_id, months in sorted(excluded, key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {well_id}: {months} months")
    
    if well_list[0] in monthly:
        print(f"\n  Example: {well_list[0]}")
        print(f"    - {len(monthly[well_list[0]])} months")
        print(f"    - Range: {monthly[well_list[0]].min():.1f} - {monthly[well_list[0]].max():.1f} m MSL")
    
    # Classify aquifers
    print("\n[6/7] Classifying aquifer types...")
    aq_info = {}
    for w in well_list:
        dom, wp, fp, mp = classify_aquifer(w, litho)
        aq_info[w] = {"dominant": dom, "wthr_pct": wp, "frac_pct": fp, "mass_pct": mp}
    
    zone_counts = pd.Series({w: v['dominant'] for w, v in aq_info.items()}).value_counts()
    print(f"  Aquifer zones: {zone_counts.to_dict()}")
    
    # Build graph
    print("\n[7/7] Building geology-informed graph...")
    adj = build_graph(well_list, wells, aq_info)
    adj_t = torch.FloatTensor(adj)
    n_edges = int((adj > 0).sum())
    print(f"  Nodes: {len(well_list)}")
    print(f"  Edges: {n_edges}")
    
    # Build node features
    print("\n[8/8] Building node features...")
    node_feat = build_node_features(well_list, wells, monthly, aq_info)
    node_feat_t = torch.FloatTensor(node_feat)
    print(f"  Node features shape: {node_feat.shape}")
    print(f"  Feature dimensions: {node_feat.shape[1]}")
    
    # Create well_to_idx mapping
    well_to_idx = {w: i for i, w in enumerate(well_list)}
    
    # Create sequences
    print("\n[9/9] Creating training sequences...")
    SEQ_LEN = 24
    HORIZON = 12
    SPLIT_YR = 2019
    
    train_X, train_y, train_wi, train_geo = [], [], [], []
    test_X, test_y, test_wi, test_geo = [], [], [], []
    scalers = {}
    
    for well_id in well_list:
        series = monthly[well_id]
        values = series.values.reshape(-1, 1)
        
        # Create MinMaxScaler for this well
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled = scaler.fit_transform(values).flatten()
        scalers[well_id] = scaler
        
        well_idx = well_to_idx[well_id]
        aq_zone = aq_info[well_id]['dominant']
        
        # Create sequences
        for i in range(len(scaled) - SEQ_LEN - HORIZON + 1):
            x = scaled[i:i+SEQ_LEN]
            y = scaled[i+SEQ_LEN:i+SEQ_LEN+HORIZON]
            
            year = series.index[i+SEQ_LEN].year
            if year < SPLIT_YR:
                train_X.append(x)
                train_y.append(y)
                train_wi.append(well_idx)
                train_geo.append(aq_zone)
            else:
                test_X.append(x)
                test_y.append(y)
                test_wi.append(well_idx)
                test_geo.append(aq_zone)
    
    # Convert to tensors
    train_X = torch.FloatTensor(np.array(train_X)).unsqueeze(-1)   # [N, SEQ_LEN, 1]
    train_y = torch.FloatTensor(np.array(train_y))                  # [N, HORIZON]
    train_wi = torch.LongTensor(train_wi)                           # [N]
    
    test_X = torch.FloatTensor(np.array(test_X)).unsqueeze(-1)
    test_y = torch.FloatTensor(np.array(test_y))
    test_wi = torch.LongTensor(test_wi)
    
    print(f"  Train sequences: {len(train_X):,}")
    print(f"  Test sequences: {len(test_X):,}")
    print(f"  Scalers created: {len(scalers)}")
    
    if scalers:
        sample_well = list(scalers.keys())[0]
        sample_scaler = scalers[sample_well]
        print(f"  Sample scaler ({sample_well}):")
        print(f"    data_min: {sample_scaler.data_min_[0]:.1f} m MSL")
        print(f"    data_max: {sample_scaler.data_max_[0]:.1f} m MSL")
        print(f"    data_range: {sample_scaler.data_range_[0]:.1f} m")
    
    # Save everything
    print("\n[10/10] Saving to ml/artifacts/...")
    os.makedirs('ml/artifacts', exist_ok=True)
    
    # Save sequences in train.py expected format
    with open('ml/artifacts/sequences.pkl', 'wb') as f:
        pickle.dump({
            'train_X': train_X,
            'train_y': train_y,
            'train_wi': train_wi,
            'train_geo': train_geo,
            'test_X': test_X,
            'test_y': test_y,
            'test_wi': test_wi,
            'test_geo': test_geo,
            'seq_len': SEQ_LEN,
            'horizon': HORIZON,
        }, f)
    
    # Save graph cache
    with open('ml/artifacts/graph_cache.pkl', 'wb') as f:
        pickle.dump({
            'adj': adj_t,
            'node_feat': node_feat_t,
            'well_to_idx': well_to_idx,
            'well_list': well_list,
        }, f)
    
    # Save scalers
    with open('ml/artifacts/scalers.pkl', 'wb') as f:
        pickle.dump(scalers, f)
    
    print("  ✓ sequences.pkl")
    print("  ✓ graph_cache.pkl")
    print("  ✓ scalers.pkl")
    
    print("\n" + "="*70)
    print("DATA PREPARATION COMPLETE!")
    print("="*70)
    print(f"Included {len(well_list)} wells (up from ~1004 with strict criteria)")
    print("Next step: python3 ml/train.py")
    print()

if __name__ == '__main__':
    main()
