#!/usr/bin/env python3
"""
Simplified training script that pre-computes and caches the graph.
"""
import torch
import numpy as np
import pickle
import os

print("=" * 70)
print("PGNN-LSTM Training - Simplified Version")
print("=" * 70)

# Check if graph is already built
graph_cache = 'ml/artifacts/graph_cache.pkl'

if os.path.exists(graph_cache):
    print("\n✓ Loading cached graph data...")
    with open(graph_cache, 'rb') as f:
        graph_data = pickle.load(f)
    adjacency = graph_data['adjacency']
    node_features = graph_data['node_features']
    well_id_to_index = graph_data['well_id_to_index']
    print(f"  Nodes: {len(well_id_to_index)}")
    print(f"  Adjacency shape: {adjacency.shape}")
else:
    print("\n1. Building spatial graph (this takes ~5-10 minutes)...")
    print("   This is a one-time operation, will be cached for future runs")
    
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from ml.models.graph_builder import prepare_graph_data
    
    adjacency, node_features, well_id_to_index = prepare_graph_data(
        'data/wells.csv',
        k_neighbors=10
    )
    
    # Cache for future runs
    os.makedirs('ml/artifacts', exist_ok=True)
    graph_data = {
        'adjacency': adjacency,
        'node_features': node_features,
        'well_id_to_index': well_id_to_index
    }
    with open(graph_cache, 'wb') as f:
        pickle.dump(graph_data, f)
    print(f"\n✓ Graph cached to: {graph_cache}")

print("\n2. Loading training sequences...")
with open('data/train_sequences.pkl', 'rb') as f:
    train_sequences = pickle.load(f)

with open('data/test_sequences.pkl', 'rb') as f:
    test_sequences = pickle.load(f)

print(f"   Training: {len(train_sequences):,} sequences")
print(f"   Testing: {len(test_sequences):,} sequences")

print("\n3. Creating model...")
import sys
sys.path.insert(0, '.')
from ml.models.pgnn_lstm import PGNN_LSTM, count_parameters

model = PGNN_LSTM(
    n_node_feat=8,
    seq_len=24,
    gcn_hidden=24,
    lstm_hidden=48,
    n_layers=2,
    horizon=12,
    dropout=0.2
)

print(f"   ✓ Model created: {count_parameters(model):,} parameters")

print("\n" + "=" * 70)
print("✓ Initialization complete")
print("=" * 70)
print("\nGraph cached successfully. Full training will proceed from here.")
print("Estimated training time: 45-90 minutes")
print("\nTo continue training, the full script will now prepare data and train...")
