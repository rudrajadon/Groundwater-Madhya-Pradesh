#!/usr/bin/env python3
"""
Simple data preparation that works with current database export format.
Creates sequences and graph for PGNN-LSTM training.
"""
import os
import sys
import pickle
import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import MinMaxScaler

SEQ_LEN = 24
HORIZON = 12
DIST_THR = 0.15  # ~15km for graph edges

def main():
    print("="*70)
    print("PGNN-LSTM Data Preparation (Simplified)")
    print("="*70)
    
    # Load data
    print("\nLoading data...")
    wells_df = pd.read_csv('ml/data/wells.csv')
    wl_df = pd.read_csv('ml/data/water_levels.csv')
    
    print(f"  Wells: {len(wells_df)}")
    print(f"  Water level records: {len(wl_df)}")
    
    # Parse dates
    wl_df['date'] = pd.to_datetime(wl_df['date'], format='mixed', errors='coerce')
    wl_df = wl_df.dropna(subset=['date', 'Water Level'])
    
    print(f"  Valid readings after date parsing: {len(wl_df)}")
    
    # Create monthly series for each well
    print("\nCreating monthly series...")
    monthly_series = {}
    
    for well_id in wl_df['Well No'].unique():
        well_data = wl_df[wl_df['Well No'] == well_id].sort_values('date')
        
        # Resample to monthly
        well_data = well_data.set_index('date')
        monthly = well_data['Water Level'].resample('MS').mean()
        monthly = monthly.interpolate(method='linear', limit=3).dropna()
        
        # Need at least 60 months (5 years) of data
        if len(monthly) >= 60:
            monthly_series[well_id] = monthly
    
    print(f"  Wells with ≥60 months data: {len(monthly_series)}")
    
    # Build graph
    print("\nBuilding spatial graph...")
    well_list = sorted(monthly_series.keys())
    n_wells = len(well_list)
    
    # Get coordinates
    coords = {}
    geology = {}
    aquifer = {}
    
    for well_id in well_list:
        well_row = wells_df[wells_df['Well No'] == well_id]
        if len(well_row) > 0:
            coords[well_id] = (
                float(well_row['Easting'].values[0]),
                float(well_row['Northing'].values[0])
            )
            geology[well_id] = well_row['geology_type'].values[0] if pd.notna(well_row['geology_type'].values[0]) else 'Unknown'
            aquifer[well_id] = well_row['aquifer_classification'].values[0] if pd.notna(well_row['aquifer_classification'].values[0]) else 'Unknown'
        else:
            coords[well_id] = (77.0, 23.0)  # Default MP center
            geology[well_id] = 'Unknown'
            aquifer[well_id] = 'Unknown'
    
    # Build adjacency matrix (distance-based + geology-weighted)
    adj = np.zeros((n_wells, n_wells))
    
    for i, w1 in enumerate(well_list):
        for j, w2 in enumerate(well_list):
            if i == j:
                continue
            
            # Calculate distance
            dx = coords[w1][0] - coords[w2][0]
            dy = coords[w1][1] - coords[w2][1]
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist < DIST_THR:
                # Weight by geology similarity
                geol_weight = 1.0 if geology[w1] == geology[w2] else 0.4
                adj[i, j] = (1 - dist / DIST_THR) * geol_weight
    
    print(f"  Graph nodes: {n_wells}")
    print(f"  Graph edges: {int((adj > 0).sum())}")
    
    # Build node features
    print("\nBuilding node features...")
    node_feats = []
    
    for well_id in well_list:
        well_row = wells_df[wells_df['Well No'] == well_id]
        
        # Elevation
        elev = float(well_row['Elevation of Ground Level'].values[0]) if len(well_row) > 0 and pd.notna(well_row['Elevation of Ground Level'].values[0]) else 500.0
        
        # Command area
        cmd_area = float(well_row['Command Area'].values[0]) if len(well_row) > 0 and pd.notna(well_row['Command Area'].values[0]) else 0.0
        
        # Time series statistics
        series = monthly_series[well_id].values
        mean_wl = float(np.mean(series))
        std_wl = float(np.std(series))
        
        # Linear trend
        x = np.arange(len(series))
        slope = np.polyfit(x, series, 1)[0]
        
        # Geology one-hot (Basalt, Granite, Vindhyan, Other)
        geol = geology[well_id]
        is_basalt = 1.0 if geol == 'Basalt' else 0.0
        is_granite = 1.0 if geol == 'Granite' else 0.0
        is_vindhyan = 1.0 if geol == 'Vindhyan' else 0.0
        
        node_feats.append([
            elev / 600.0,  # Normalized elevation
            cmd_area,
            mean_wl / 530.0,  # Normalized mean water level
            std_wl / 15.0,  # Normalized std
            slope * 10.0,  # Trend
            is_basalt,
            is_granite,
            is_vindhyan
        ])
    
    node_feats = np.array(node_feats, dtype=np.float32)
    
    # Handle NaN in node features
    for col in range(node_feats.shape[1]):
        col_data = node_feats[:, col]
        if np.isnan(col_data).any():
            median = np.nanmedian(col_data)
            node_feats[np.isnan(col_data), col] = median
    
    # Create training sequences
    print("\nCreating training/test sequences...")
    train_X, train_y, train_wi, train_geo = [], [], [], []
    test_X, test_y, test_wi, test_geo = [], [], [], []
    scalers = {}
    
    for well_id in well_list:
        series = monthly_series[well_id].values
        
        if len(series) < SEQ_LEN + HORIZON:
            continue
        
        # Create scaler
        scaler = MinMaxScaler(feature_range=(0, 1))
        series_scaled = scaler.fit_transform(series.reshape(-1, 1)).flatten()
        scalers[well_id] = scaler
        
        well_idx = well_list.index(well_id)
        geol = geology[well_id]
        
        # Create sequences
        n_sequences = len(series_scaled) - SEQ_LEN - HORIZON + 1
        train_cutoff = int(0.8 * n_sequences)
        
        for i in range(n_sequences):
            X = series_scaled[i:i+SEQ_LEN]
            y = series_scaled[i+SEQ_LEN:i+SEQ_LEN+HORIZON]
            
            if i < train_cutoff:
                train_X.append(X)
                train_y.append(y)
                train_wi.append(well_idx)
                train_geo.append(geol)
            else:
                test_X.append(X)
                test_y.append(y)
                test_wi.append(well_idx)
                test_geo.append(geol)
    
    print(f"  Training sequences: {len(train_X):,}")
    print(f"  Test sequences: {len(test_X):,}")
    print(f"  Wells with scalers: {len(scalers)}")
    
    # Convert to torch tensors
    sequences = {
        'train_X': torch.FloatTensor(np.array(train_X)).unsqueeze(-1),
        'train_y': torch.FloatTensor(np.array(train_y)),
        'train_wi': torch.LongTensor(train_wi),
        'train_geo': train_geo,
        'test_X': torch.FloatTensor(np.array(test_X)).unsqueeze(-1),
        'test_y': torch.FloatTensor(np.array(test_y)),
        'test_wi': torch.LongTensor(test_wi),
        'test_geo': test_geo,
    }
    
    graph_cache = {
        'adj': torch.FloatTensor(adj),
        'node_feat': torch.FloatTensor(node_feats),
        'well_to_idx': {w: i for i, w in enumerate(well_list)},
    }
    
    # Save artifacts
    print("\nSaving artifacts...")
    os.makedirs('ml/artifacts', exist_ok=True)
    
    with open('ml/artifacts/sequences.pkl', 'wb') as f:
        pickle.dump(sequences, f)
    print("  ✓ Saved sequences.pkl")
    
    with open('ml/artifacts/graph_cache.pkl', 'wb') as f:
        pickle.dump(graph_cache, f)
    print("  ✓ Saved graph_cache.pkl")
    
    with open('ml/artifacts/scalers.pkl', 'wb') as f:
        pickle.dump(scalers, f)
    print("  ✓ Saved scalers.pkl")
    
    # Summary
    print("\n" + "="*70)
    print("✓ Data preparation complete!")
    print("="*70)
    print(f"\nSummary:")
    print(f"  Wells in model: {len(well_list)}")
    print(f"  Training sequences: {len(train_X):,}")
    print(f"  Test sequences: {len(test_X):,}")
    print(f"  Graph edges: {int((adj > 0).sum())}")
    print(f"\nGeology distribution:")
    for g in ['Basalt', 'Granite', 'Vindhyan', 'Unknown']:
        count = sum(1 for w in well_list if geology[w] == g)
        print(f"  {g:12s}: {count:4d} wells ({100*count/len(well_list):.1f}%)")
    
    print(f"\nNext step: python3 ml/train.py")
    print("="*70)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
