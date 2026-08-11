"""
Serving-time inference wrapper. Loads the locked v3 model + fitted scalers
and exposes predict_well() / predict_point() for the FastAPI backend.

MC-Dropout uncertainty: re-runs the forward pass N times with dropout left
ON (model.train() mode restricted to dropout layers) and reports the spread
— same technique prototyped in the notebook's Cell G, packaged here as a
reusable function instead of one-off notebook code.
"""
import json
import os
import threading

import numpy as np
import torch

from model import PGNN_LSTM
from preprocessing import HORIZON, SEQ_LEN, edge_weight

MC_SAMPLES = 30


class ForecastModel:
    def __init__(self, artifact_dir: str):
        with open(os.path.join(artifact_dir, "model_metadata.json")) as f:
            self.meta = json.load(f)
        self.well_list = self.meta["well_list"]

        # Load model
        self.model = PGNN_LSTM(n_node_feat=8)
        model_path = os.path.join(artifact_dir, os.path.basename(self.meta["artifact_path"]))
        self.model.load_state_dict(torch.load(model_path, map_location="cpu"))
        self.model.eval()
        self._mc_lock = threading.Lock()
        
        # Load global scaler
        scaler_path = os.path.join(artifact_dir, "scaler.joblib")
        if os.path.exists(scaler_path):
            import joblib
            self.global_scaler = joblib.load(scaler_path)
        else:
            # Fallback: try old per-well scalers for backward compatibility
            scalers_path = os.path.join(artifact_dir, "scalers.joblib")
            if os.path.exists(scalers_path):
                import joblib
                self.global_scaler = None
                self.scalers = joblib.load(scalers_path)
            else:
                self.global_scaler = None
                self.scalers = {}
        
        # Load pre-built graph structure (node features + adjacency matrix)
        graph_path = os.path.join(artifact_dir, "graph_structure.npz")
        if os.path.exists(graph_path):
            graph_data = np.load(graph_path, allow_pickle=True)
            self._node_feat = torch.FloatTensor(graph_data['node_feats'])
            self._adj = torch.FloatTensor(graph_data['adj'])
            
            # Rebuild aq_info dict
            self._aq_info = {}
            well_list_from_graph = graph_data['well_list']
            aq_info_arr = graph_data['aq_info']
            for well, info_dict in zip(well_list_from_graph, aq_info_arr):
                self._aq_info[str(well)] = dict(info_dict)
            
            print(f"[ForecastModel] Loaded graph: {len(well_list_from_graph)} wells, "
                  f"{self._node_feat.shape[1]} features, adj shape {self._adj.shape}")
        else:
            print(f"[ForecastModel] WARNING: No graph_structure.npz found - predictions will be poor!")
            self._node_feat = None
            self._adj = None
            self._aq_info = {}

    def _forward_mc(self, x, node_feat, adj, well_idx, aq_cls, n_samples=MC_SAMPLES):
        with self._mc_lock:
            self.model.train()  # enables dropout for MC sampling
            preds = []
            with torch.no_grad():
                for _ in range(n_samples):
                    preds.append(self.model(x, node_feat, adj, well_idx, aq_cls).numpy())
            self.model.eval()
        preds = np.stack(preds)  # (n_samples, batch, horizon)
        return preds.mean(axis=0), preds.std(axis=0)

    def predict_well(self, well_id: str, recent_scaled_series: np.ndarray,
                      node_feat: torch.Tensor, adj: torch.Tensor,
                      aquifer_zone: str, scaler=None) -> dict:
        """recent_scaled_series: last SEQ_LEN months, already StandardScaler-scaled
        with the global scaler used at train time (pass via scaler arg, or uses
        self.global_scaler if available)."""
        if len(recent_scaled_series) != SEQ_LEN:
            raise ValueError(f"Expected {SEQ_LEN} months of history, got {len(recent_scaled_series)}")

        if scaler is None:
            scaler = self.global_scaler
            if scaler is None:
                # Fallback to per-well scaler for backward compatibility
                scaler = self.scalers.get(well_id)
                if scaler is None:
                    raise ValueError(f"No scaler found for well {well_id}")

        wi = self.well_list.index(well_id) if well_id in self.well_list else 0
        x = torch.FloatTensor(recent_scaled_series.reshape(1, SEQ_LEN, 1))
        wib = torch.tensor([wi], dtype=torch.long)

        mean_scaled, std_scaled = self._forward_mc(x, node_feat, adj, wib, [aquifer_zone])
        mean = scaler.inverse_transform(mean_scaled).flatten()
        # For StandardScaler: std in original units = std_scaled * scaler.scale_
        std = (std_scaled.flatten() * scaler.scale_[0])

        return {
            "well_id": well_id,
            "horizon_months": HORIZON,
            "forecast_head_msl": [round(float(v), 2) for v in mean],
            "uncertainty_std_m": [round(float(v), 2) for v in std],
        }

    def predict_point(self, lat: float, lon: float, aquifer_zone: str,
                      block: str, recent_scaled_series: np.ndarray,
                      node_feat: torch.Tensor, adj: torch.Tensor,
                      scaler, existing_coords: list, existing_zones: list,
                      existing_blocks: list) -> dict:
        """Forecast for an arbitrary GPS point not in the well graph.
        Dynamically extends the adjacency matrix with the new point's edges
        (Section 4.3/4.5 of the project plan).
        
        recent_scaled_series: already scaled with the global StandardScaler."""
        if len(recent_scaled_series) != SEQ_LEN:
            raise ValueError(f"Expected {SEQ_LEN} months of history, got {len(recent_scaled_series)}")

        if scaler is None:
            scaler = self.global_scaler

        # Compute edge weights from new point to all existing wells
        point_coord = (lon, lat)  # edge_weight uses (easting, northing) ~ (lon, lat)
        new_edges = self.extend_graph_for_point(
            point_coord, aquifer_zone, block,
            existing_coords, existing_zones, existing_blocks
        )

        # Build extended adjacency: add new node as last row/column
        n = adj.shape[0]
        ext_adj = torch.zeros(n + 1, n + 1)
        ext_adj[:n, :n] = adj
        edge_t = torch.FloatTensor(new_edges)
        ext_adj[n, :n] = edge_t
        ext_adj[:n, n] = edge_t  # symmetric

        # Extend node features: use median of existing features as placeholder
        new_feat = node_feat.mean(dim=0, keepdim=True)
        ext_node_feat = torch.cat([node_feat, new_feat], dim=0)

        # New point is at index n (last node)
        wi = n
        x = torch.FloatTensor(recent_scaled_series.reshape(1, SEQ_LEN, 1))
        wib = torch.tensor([wi], dtype=torch.long)

        mean_scaled, std_scaled = self._forward_mc(x, ext_node_feat, ext_adj, wib, [aquifer_zone])
        mean = scaler.inverse_transform(mean_scaled).flatten()
        std = (std_scaled.flatten() * scaler.scale_[0])

        return {
            "well_id": f"POINT_{lat:.4f}_{lon:.4f}",
            "horizon_months": HORIZON,
            "forecast_head_msl": [round(float(v), 2) for v in mean],
            "uncertainty_std_m": [round(float(v), 2) for v in std],
        }

    def extend_graph_for_point(self, point_coord, point_zone, point_block,
                                existing_coords, existing_zones, existing_blocks):
        """Build the extra row/column of the adjacency matrix for a new
        lat/lon point not in well_list, using the exact same edge_weight
        rule the model was trained with (preprocessing.edge_weight).
        Returns a 1D array of edge weights to each existing node."""
        return np.array([
            edge_weight(point_coord, c, point_zone, z, point_block, b)
            for c, z, b in zip(existing_coords, existing_zones, existing_blocks)
        ])
