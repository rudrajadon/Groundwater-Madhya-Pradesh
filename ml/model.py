"""
PGNN-LSTM model definition — extracted verbatim from
PGNN_LSTM_Final_ReviewerCorrected.ipynb, Cell D (cell 10).

LOCKED PRODUCTION VERSION: v3, no-rain (243k params). This is the variant
with the best measured performance (RMSE 3.40m, R2 0.65) from the actual
notebook run — NOT the rainfall-enhanced "final" variant, which underperformed
it (R2 0.56) in the notebook's own evaluation. The rainfall variant's model
class lives in ml/experimental/ and is not wired into serving.

Requires: torch (not installed in the planning sandbox — install in your
own training/serving environment: `pip install torch`).
"""
import torch
import torch.nn as nn


class GraphConv(nn.Module):
    def __init__(self, in_f, out_f):
        super().__init__()
        self.W = nn.Linear(in_f, out_f, bias=True)
        self.act = nn.ELU()

    def forward(self, x, adj):
        deg = adj.sum(1, keepdim=True).clamp(min=1e-6)
        adj_n = adj / deg
        agg = torch.mm(adj_n, x)
        return self.act(self.W(agg))


class GeolLSTM(nn.Module):
    def __init__(self, in_f, hid, layers, drop):
        super().__init__()
        self.lstm = nn.LSTM(in_f, hid, layers, batch_first=True,
                             dropout=drop if layers > 1 else 0.0)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.drop(out)


class PGNN_LSTM(nn.Module):
    """Physics-Guided Graph Neural Network LSTM.
    Target: Hydraulic head (m MSL), not depth BGL.
    
    VERSION 2: With rainfall features
    - Node features: 9 (was 8) - added avg_rainfall
    - Sequence input: [B, 24, 2] (was [B, 24, 1]) - added rainfall channel
    """

    def __init__(self, n_node_feat=9, seq_len=24, gcn_h=24, lstm_h=48,
                 n_layers=2, horizon=12, drop=0.2, use_rainfall=True):
        super().__init__()
        self.seq_len = seq_len
        self.horizon = horizon
        self.gcn_h = gcn_h
        self.use_rainfall = use_rainfall

        self.gcn1 = GraphConv(n_node_feat, gcn_h)
        self.gcn2 = GraphConv(gcn_h, gcn_h)
        self.gnorm = nn.LayerNorm(gcn_h)

        # UPDATED: LSTM input now includes rainfall
        lstm_in = (2 if use_rainfall else 1) + gcn_h  # water_level + rainfall + gcn_features
        self.lstm_W = GeolLSTM(lstm_in, lstm_h, n_layers, drop)
        self.lstm_F = GeolLSTM(lstm_in, lstm_h, n_layers, drop)
        self.lstm_M = GeolLSTM(lstm_in, lstm_h, n_layers, drop)
        self.lstm_O = GeolLSTM(lstm_in, lstm_h, n_layers, drop)

        self.attn = nn.MultiheadAttention(lstm_h, num_heads=4, dropout=drop, batch_first=True)
        self.anorm = nn.LayerNorm(lstm_h)

        self.fc1 = nn.Linear(lstm_h, lstm_h // 2)
        self.fc2 = nn.Linear(lstm_h // 2, horizon)
        self.drop = nn.Dropout(drop)
        self.relu = nn.ReLU()

    def _get_lstm(self, cls):
        return {"Weathered": self.lstm_W, "Fractured": self.lstm_F,
                "Massive": self.lstm_M}.get(cls, self.lstm_O)

    def forward(self, wl_seq, node_f, adj, well_idx, aq_cls):
        g = self.gnorm(self.gcn2(self.gcn1(node_f, adj), adj))
        sp = g[well_idx].unsqueeze(1).expand(-1, self.seq_len, -1)
        x = torch.cat([wl_seq, sp], dim=-1)

        B = x.shape[0]
        # Collect LSTM outputs per geology group, then reassemble by original order
        # (avoids in-place tensor assignment that breaks autograd on GPU)
        grp = {}
        for i, c in enumerate(aq_cls):
            grp.setdefault(c, []).append(i)
        parts = []  # (original_indices, lstm_output) pairs
        for c, idx in grp.items():
            o = self._get_lstm(c)(x[idx])
            parts.append((idx, o))
        # Reconstruct output tensor in original sample order
        order = [None] * B
        for idx_list, o in parts:
            for pos, orig_i in enumerate(idx_list):
                order[orig_i] = o[pos:pos+1]
        out = torch.cat(order, dim=0)

        a, _ = self.attn(out, out, out)
        out = self.anorm(out + a)
        final = out[:, -1, :]
        return self.fc2(self.relu(self.fc1(self.drop(final))))


class PhysicsLoss(nn.Module):
    """L = MSE + lam1*Darcy_smoothness + lam2*WaterBalance + lam3*MassConserv
    (targets are hydraulic head in m MSL, per notebook FIX-1/FIX-6)."""

    def __init__(self, lam1=0.08, lam2=0.04, lam3=0.02):
        super().__init__()
        self.lam1, self.lam2, self.lam3 = lam1, lam2, lam3
        self.mse = nn.MSELoss()

    def forward(self, pred, target):
        mse = self.mse(pred, target)
        smooth = torch.mean((pred[:, 1:] - pred[:, :-1]) ** 2)
        if pred.shape[1] >= 9:
            mon_chg = pred[:, 8] - pred[:, 4]
            wbal = torch.clamp(-mon_chg, min=0).mean()
        else:
            wbal = torch.tensor(0.0, device=pred.device)
        mass = torch.clamp(pred.abs() - 600.0, min=0).mean()
        total = mse + self.lam1 * smooth + self.lam2 * wbal + self.lam3 * mass
        return total, {"mse": mse.item(), "smooth": smooth.item(),
                        "wbal": wbal.item(), "mass": mass.item()}
