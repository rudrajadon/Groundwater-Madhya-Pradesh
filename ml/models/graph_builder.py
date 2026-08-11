"""
Spatial graph builder for PGNN-LSTM.
Builds k-NN adjacency weighted by inverse-distance + elevation similarity.
Caches result so it is only computed once.
"""
import os
import pickle
import numpy as np
import pandas as pd
import torch
from scipy.spatial.distance import cdist


# ── cache path ────────────────────────────────────────────────────────────────
_CACHE = os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'graph_cache.pkl')


def build_spatial_graph(wells_df: pd.DataFrame,
                         k_neighbors: int = 10,
                         elev_weight: float = 0.3):
    """
    Build k-NN graph with edge weights:
        w = (1 - elev_weight) * dist_weight  +  elev_weight * elev_similarity
    where dist_weight = 1 / (1 + d/10)  (d in degrees, ~1° ≈ 111 km)
    and   elev_sim    = 1 / (1 + |Δh|/50)  (h in metres)

    Returns
    -------
    adj : np.ndarray  [N, N]  float32
    well_to_idx : dict  well_id → integer index
    """
    valid = wells_df.dropna(subset=['Northing', 'Easting']).copy().reset_index(drop=True)
    N = len(valid)

    col_elev = 'Elevation of Ground Level'
    med_elev  = valid[col_elev].median()
    elevs     = valid[col_elev].fillna(med_elev).values.astype(np.float32)
    coords    = valid[['Northing', 'Easting']].values.astype(np.float32)

    print(f"  Computing {N}×{N} distance matrix …", flush=True)
    dist_mat  = cdist(coords, coords, metric='euclidean').astype(np.float32)
    elev_diff = np.abs(elevs[:, None] - elevs[None, :]).astype(np.float32)

    dist_w    = 1.0 / (1.0 + dist_mat  / 1.0)   # 1° ≈ 111 km; keep 1 for sensitivity
    elev_sim  = 1.0 / (1.0 + elev_diff / 50.0)
    weight_mat = (1 - elev_weight) * dist_w + elev_weight * elev_sim

    adj = np.zeros((N, N), dtype=np.float32)
    print(f"  Building k={k_neighbors} neighbours …", flush=True)
    for i in range(N):
        row = weight_mat[i].copy()
        row[i] = -np.inf                           # exclude self
        top_k = np.argpartition(row, -k_neighbors)[-k_neighbors:]
        adj[i, top_k] = row[top_k]

    # symmetric + self-loops
    adj = np.maximum(adj, adj.T)
    np.fill_diagonal(adj, 1.0)

    well_to_idx = {str(w): i for i, w in enumerate(valid['Well No'])}

    n_edges = int((adj > 0).sum() - N)
    print(f"  Nodes={N}  Edges={n_edges}  Mean degree={n_edges/N:.1f}")
    return adj, well_to_idx


def build_node_features(wells_df: pd.DataFrame, well_to_idx: dict) -> np.ndarray:
    """
    8-dimensional static node features per well:
      [0] Northing  (normalised)
      [1] Easting   (normalised)
      [2] Elevation (normalised)
      [3] Command Area flag (0/1)
      [4] Weathered aquifer (0/1)
      [5] Fractured aquifer (0/1)
      [6] Unknown  aquifer  (0/1)   ← Massive maps to all-zero
      [7] Depth placeholder         (0.5)
    """
    N    = len(well_to_idx)
    feat = np.zeros((N, 8), dtype=np.float32)
    col  = 'Elevation of Ground Level'

    lat_min, lat_rng = 20.0, 8.0
    lon_min, lon_rng = 74.0, 10.0
    elev_min, elev_rng = 100.0, 800.0

    for wid, idx in well_to_idx.items():
        rows = wells_df[wells_df['Well No'] == wid]
        if rows.empty:
            continue
        r = rows.iloc[0]

        feat[idx, 0] = (r['Northing']  - lat_min)  / lat_rng
        feat[idx, 1] = (r['Easting']   - lon_min)  / lon_rng
        feat[idx, 2] = (r.get(col, 400) - elev_min) / elev_rng

        ca = str(r.get('Command Area', '')).strip().lower()
        feat[idx, 3] = 1.0 if ca in ('yes', 'y', '1', 'true') else 0.0

        aq = str(r.get('aquifer_classification', '')).strip()
        if aq == 'Weathered':  feat[idx, 4] = 1.0
        elif aq == 'Fractured': feat[idx, 5] = 1.0
        elif aq == 'Unknown':   feat[idx, 6] = 1.0

        feat[idx, 7] = 0.5   # depth placeholder

    return feat


def prepare_graph_data(wells_csv: str, k_neighbors: int = 10, force_rebuild: bool = False):
    """
    Load (or build + cache) graph tensors.

    Returns
    -------
    adj_t         : FloatTensor [N, N]
    node_feat_t   : FloatTensor [N, 8]
    well_to_idx   : dict
    """
    cache_path = os.path.abspath(_CACHE)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    if os.path.exists(cache_path) and not force_rebuild:
        print(f"  Loading cached graph from {cache_path}", flush=True)
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)
        adj_t       = data['adj']
        node_feat_t = data['node_feat']
        well_to_idx = data['well_to_idx']
        print(f"  ✓ Graph loaded: {len(well_to_idx)} nodes", flush=True)
        return adj_t, node_feat_t, well_to_idx

    print(f"  Building graph from {wells_csv} …", flush=True)
    wells_df = pd.read_csv(wells_csv)

    adj, well_to_idx = build_spatial_graph(wells_df, k_neighbors=k_neighbors)
    node_feat        = build_node_features(wells_df, well_to_idx)

    adj_t       = torch.FloatTensor(adj)
    node_feat_t = torch.FloatTensor(node_feat)

    with open(cache_path, 'wb') as f:
        pickle.dump({'adj': adj_t, 'node_feat': node_feat_t,
                     'well_to_idx': well_to_idx}, f)
    print(f"  ✓ Graph cached to {cache_path}", flush=True)
    return adj_t, node_feat_t, well_to_idx
