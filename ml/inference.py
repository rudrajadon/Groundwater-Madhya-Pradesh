"""
PGNN-LSTM inference wrapper for the FastAPI backend.

Loaded once at startup by backend/app/main.py via:
    from inference import ForecastModel
    app.state.model = ForecastModel(artifact_dir)

Public API (unchanged contract vs old inference.py):
    model.predict_well(well_id, scaled_series, node_feat, adj, zone, scaler)
    model.predict_point(lat, lon, zone, block, scaled_series, ...)
    model.well_list   – list[str]  all trained well_ids
    model.meta        – dict       from model_metadata.json
    model._node_feat  – FloatTensor [N, 8]
    model._adj        – FloatTensor [N, N]
"""
import json
import os
import pickle
import threading

import numpy as np
import torch
import torch.nn as nn

SEQ_LEN = 24
HORIZON = 12
MC_SAMPLES = 20


# ── model architecture (must stay in sync with ml/train.py) ──────────────────

class GraphConv(nn.Module):
    def __init__(self, in_f, out_f):
        super().__init__()
        self.W = nn.Linear(in_f, out_f, bias=True)
        self.act = nn.ELU()

    def forward(self, x, adj):
        deg = adj.sum(1, keepdim=True).clamp(min=1e-6)
        return self.act(self.W(torch.mm(adj / deg, x)))


class GeolLSTM(nn.Module):
    def __init__(self, in_f, hid, layers, drop):
        super().__init__()
        self.lstm = nn.LSTM(in_f, hid, layers, batch_first=True,
                            dropout=drop if layers > 1 else 0.)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.drop(out)


class PGNN_LSTM(nn.Module):
    GCN_H = 24; LSTM_H = 48; LAYERS = 2; DROP = 0.2
    SEQ_LEN = SEQ_LEN; HORIZON = HORIZON; N_FEAT = 8

    def __init__(self):
        super().__init__()
        self.gcn1  = GraphConv(self.N_FEAT, self.GCN_H)
        self.gcn2  = GraphConv(self.GCN_H,  self.GCN_H)
        self.gnorm = nn.LayerNorm(self.GCN_H)
        lin = 1 + self.GCN_H
        self.lstm_B = GeolLSTM(lin, self.LSTM_H, self.LAYERS, self.DROP)
        self.lstm_G = GeolLSTM(lin, self.LSTM_H, self.LAYERS, self.DROP)
        self.lstm_V = GeolLSTM(lin, self.LSTM_H, self.LAYERS, self.DROP)
        self.lstm_U = GeolLSTM(lin, self.LSTM_H, self.LAYERS, self.DROP)
        self.attn  = nn.MultiheadAttention(self.LSTM_H, num_heads=4,
                                            dropout=self.DROP, batch_first=True)
        self.anorm = nn.LayerNorm(self.LSTM_H)
        self.fc1   = nn.Linear(self.LSTM_H, self.LSTM_H // 2)
        self.fc2   = nn.Linear(self.LSTM_H // 2, self.HORIZON)
        self.drop  = nn.Dropout(self.DROP)
        self.relu  = nn.ReLU()

    def _lstm(self, geo):
        return {'Basalt': self.lstm_B,
                'Granite': self.lstm_G,
                'Vindhyan': self.lstm_V}.get(geo, self.lstm_U)

    def gcn_embed(self, nf, adj):
        return self.gnorm(self.gcn2(self.gcn1(nf, adj), adj))

    def forward_with_embed(self, wl, g_embed, wi, geo_list):
        B  = wl.shape[0]
        sp = g_embed[wi].unsqueeze(1).expand(-1, self.SEQ_LEN, -1)
        x  = torch.cat([wl, sp], dim=-1)
        out = torch.zeros(B, self.SEQ_LEN, self.LSTM_H, device=wl.device)
        grp: dict = {}
        for i, g in enumerate(geo_list):
            grp.setdefault(g, []).append(i)
        for g, idx in grp.items():
            out[idx] = self._lstm(g)(x[idx])
        a, _ = self.attn(out, out, out)
        out  = self.anorm(out + a)
        h    = out[:, -1, :]
        return self.fc2(self.relu(self.fc1(self.drop(h))))

    def forward(self, wl, nf, adj, wi, geo_list):
        return self.forward_with_embed(wl, self.gcn_embed(nf, adj), wi, geo_list)


# ── ForecastModel ─────────────────────────────────────────────────────────────

class ForecastModel:
    """
    Loads trained PGNN-LSTM weights, graph cache, and per-well scalers.
    Thread-safe: MC-dropout sampling uses a lock.
    """

    def __init__(self, artifact_dir: str):
        self._lock = threading.Lock()

        # ── metadata ──────────────────────────────────────────────────────────
        meta_path = os.path.join(artifact_dir, 'model_metadata.json')
        with open(meta_path) as f:
            self.meta = json.load(f)

        # ── model weights ─────────────────────────────────────────────────────
        ckpt_path = os.path.join(artifact_dir, 'pgnn_lstm_best.pt')
        self._model = PGNN_LSTM()
        ckpt = torch.load(ckpt_path, map_location='cpu')
        self._model.load_state_dict(ckpt['model_state'])
        self._model.eval()
        print(f'[ForecastModel] Loaded PGNN-LSTM from epoch {ckpt["epoch"]} '
              f'(val_loss={ckpt["val_loss"]:.5f})')

        # ── graph ─────────────────────────────────────────────────────────────
        graph_path = os.path.join(artifact_dir, 'graph_cache.pkl')
        with open(graph_path, 'rb') as f:
            gc = pickle.load(f)
        self._adj       = gc['adj']        # FloatTensor [N, N]
        self._node_feat = gc['node_feat']  # FloatTensor [N, 8]
        self._well_to_idx = gc['well_to_idx']   # {well_id: int}
        self._idx_to_well = {v: k for k, v in self._well_to_idx.items()}
        print(f'[ForecastModel] Graph: {len(self._well_to_idx)} nodes')

        # ── scalers ───────────────────────────────────────────────────────────
        scalers_path = os.path.join(artifact_dir, 'scalers.pkl')
        with open(scalers_path, 'rb') as f:
            self._scalers = pickle.load(f)   # {well_id: MinMaxScaler}
        print(f'[ForecastModel] Scalers: {len(self._scalers)} wells')

        # Pre-compute GCN embedding (graph is static — never changes at serve time)
        with torch.no_grad():
            self._g_embed = self._model.gcn_embed(self._node_feat, self._adj)

        # Public attributes expected by forecast.py router
        self.well_list = list(self._well_to_idx.keys())
        # global_scaler not used (per-well MinMaxScalers); set None for compat
        self.global_scaler = None

    # ── internal MC-dropout forward ───────────────────────────────────────────

    def _mc_forward(self, x: torch.Tensor, g_embed: torch.Tensor,
                    wi: torch.Tensor, geo_list: list, n: int = MC_SAMPLES):
        """
        Run n stochastic forward passes with dropout ON.
        Returns (mean, std) both shape [batch, horizon] as numpy arrays.
        """
        with self._lock:
            self._model.train()   # activates dropout
            preds = []
            with torch.no_grad():
                for _ in range(n):
                    p = self._model.forward_with_embed(x, g_embed, wi, geo_list)
                    preds.append(p.numpy())
            self._model.eval()

        preds = np.stack(preds)   # [n, batch, horizon]
        return preds.mean(axis=0), preds.std(axis=0)

    # ── public API ────────────────────────────────────────────────────────────

    def predict_well(self, well_id: str,
                     recent_scaled_series: np.ndarray,
                     node_feat, adj,            # kept for API compat, ignored
                     aquifer_zone: str,
                     scaler=None) -> dict:
        """
        Forecast for a well that is in the training graph.

        recent_scaled_series : 1-D array of length SEQ_LEN,
                                already scaled with THIS well's MinMaxScaler.
        scaler               : MinMaxScaler for inverse-transform.
                                If None, falls back to self._scalers[well_id].
        """
        if well_id not in self._well_to_idx:
            raise ValueError(f"Well '{well_id}' not in trained graph")

        if scaler is None:
            scaler = self._scalers.get(well_id)
        if scaler is None:
            raise ValueError(f"No scaler for well '{well_id}'")

        wi  = torch.tensor([self._well_to_idx[well_id]], dtype=torch.long)
        x   = torch.FloatTensor(recent_scaled_series.reshape(1, SEQ_LEN, 1))
        geo = [aquifer_zone if aquifer_zone in ('Basalt','Granite','Vindhyan') else 'Unknown']

        mean_sc, std_sc = self._mc_forward(x, self._g_embed, wi, geo)

        # Inverse-transform: MinMaxScaler expects shape [n, 1]
        mean_m = scaler.inverse_transform(mean_sc.reshape(-1, 1)).flatten()
        # std in original units = std_scaled / (scaler.data_range_ + ε)
        scale  = float(scaler.data_range_[0]) if scaler.data_range_[0] > 0 else 1.0
        std_m  = std_sc.flatten() * scale

        return {
            'well_id':          well_id,
            'horizon_months':   HORIZON,
            'forecast_head_msl': [round(float(v), 2) for v in mean_m],
            'uncertainty_std_m': [round(float(v), 2) for v in std_m],
        }

    def predict_point(self, lat: float, lon: float,
                      aquifer_zone: str, block: str,
                      recent_scaled_series: np.ndarray,
                      node_feat, adj,
                      scaler,
                      existing_coords: list,
                      existing_zones: list,
                      existing_blocks: list) -> dict:
        """
        Forecast for an arbitrary GPS point not in the training graph.
        Dynamically appends the new node to the graph and runs inference.
        """
        N = self._adj.shape[0]

        # Build edge weights to all existing nodes using inverse-distance
        new_coord = np.array([lat, lon])
        import pandas as pd
        wells_coords = np.array([[0, 0]] * N, dtype=np.float32)
        for wid, idx in self._well_to_idx.items():
            c = existing_coords[idx] if idx < len(existing_coords) else (lon, lat)
            wells_coords[idx] = [c[1], c[0]]  # [lat, lon]

        dists = np.linalg.norm(wells_coords - new_coord, axis=1)
        edge_weights = (1.0 / (1.0 + dists / 1.0)).astype(np.float32)

        # Extend adjacency
        ext_adj = torch.zeros(N + 1, N + 1)
        ext_adj[:N, :N] = self._adj
        ew = torch.FloatTensor(edge_weights)
        ext_adj[N, :N] = ew
        ext_adj[:N, N] = ew

        # Extend node features (use mean of existing nodes)
        new_feat = self._node_feat.mean(dim=0, keepdim=True)
        ext_nf   = torch.cat([self._node_feat, new_feat], dim=0)

        # Recompute GCN embedding with extended graph
        with torch.no_grad():
            ext_embed = self._model.gcn_embed(ext_nf, ext_adj)

        wi  = torch.tensor([N], dtype=torch.long)
        x   = torch.FloatTensor(recent_scaled_series.reshape(1, SEQ_LEN, 1))
        geo = [aquifer_zone if aquifer_zone in ('Basalt', 'Granite', 'Vindhyan') else 'Unknown']

        mean_sc, std_sc = self._mc_forward(x, ext_embed, wi, geo)

        if scaler is not None:
            mean_m = scaler.inverse_transform(mean_sc.reshape(-1, 1)).flatten()
            scale  = float(scaler.data_range_[0]) if scaler.data_range_[0] > 0 else 1.0
            std_m  = std_sc.flatten() * scale
        else:
            mean_m = mean_sc.flatten()
            std_m  = std_sc.flatten()

        return {
            'well_id':          f'POINT_{lat:.4f}_{lon:.4f}',
            'horizon_months':   HORIZON,
            'forecast_head_msl': [round(float(v), 2) for v in mean_m],
            'uncertainty_std_m': [round(float(v), 2) for v in std_m],
        }
