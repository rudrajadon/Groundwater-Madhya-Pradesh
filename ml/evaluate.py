#!/usr/bin/env python3
"""
Evaluate the trained PGNN-LSTM on the held-out test set.
Produces per-well metrics (RMSE, MAE, R², NSE) and saves results.

Run:  python ml/evaluate.py
Out:  ml/artifacts/evaluation_results.csv
      ml/artifacts/evaluation_summary.json
"""
import os, sys, json, pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

sys.stdout.reconfigure(line_buffering=True)
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, 'ml', 'artifacts')
sys.path.insert(0, ROOT)

# ── inline model (must match train.py exactly) ────────────────────────────────
class GraphConv(nn.Module):
    def __init__(self, in_f, out_f):
        super().__init__()
        self.W = nn.Linear(in_f, out_f, bias=True); self.act = nn.ELU()
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
        out, _ = self.lstm(x); return self.drop(out)

class PGNN_LSTM(nn.Module):
    GCN_H=24; LSTM_H=48; LAYERS=2; DROP=0.2; SEQ_LEN=24; HORIZON=12; N_FEAT=8
    def __init__(self):
        super().__init__()
        self.gcn1=GraphConv(self.N_FEAT,self.GCN_H)
        self.gcn2=GraphConv(self.GCN_H,self.GCN_H)
        self.gnorm=nn.LayerNorm(self.GCN_H)
        lin=1+self.GCN_H
        self.lstm_B=GeolLSTM(lin,self.LSTM_H,self.LAYERS,self.DROP)
        self.lstm_G=GeolLSTM(lin,self.LSTM_H,self.LAYERS,self.DROP)
        self.lstm_V=GeolLSTM(lin,self.LSTM_H,self.LAYERS,self.DROP)
        self.lstm_U=GeolLSTM(lin,self.LSTM_H,self.LAYERS,self.DROP)
        self.attn=nn.MultiheadAttention(self.LSTM_H,num_heads=4,dropout=self.DROP,batch_first=True)
        self.anorm=nn.LayerNorm(self.LSTM_H)
        self.fc1=nn.Linear(self.LSTM_H,self.LSTM_H//2)
        self.fc2=nn.Linear(self.LSTM_H//2,self.HORIZON)
        self.drop=nn.Dropout(self.DROP); self.relu=nn.ReLU()
    def _lstm(self,g):
        return {'Basalt':self.lstm_B,'Granite':self.lstm_G,'Vindhyan':self.lstm_V}.get(g,self.lstm_U)
    def gcn_embed(self,nf,adj):
        return self.gnorm(self.gcn2(self.gcn1(nf,adj),adj))
    def forward(self,wl,nf,adj,wi,geo):
        g=self.gcn_embed(nf,adj); sp=g[wi].unsqueeze(1).expand(-1,self.SEQ_LEN,-1)
        x=torch.cat([wl,sp],dim=-1)
        B=x.shape[0]; out=torch.zeros(B,self.SEQ_LEN,self.LSTM_H)
        grp={}
        for i,g_ in enumerate(geo): grp.setdefault(g_,[]).append(i)
        for g_,idx in grp.items(): out[idx]=self._lstm(g_)(x[idx])
        a,_=self.attn(out,out,out); out=self.anorm(out+a)
        return self.fc2(self.relu(self.fc1(self.drop(out[:,-1,:]))))
# ─────────────────────────────────────────────────────────────────────────────

def nse(y_true, y_pred):
    """Nash-Sutcliffe Efficiency."""
    denom = np.sum((y_true - y_true.mean()) ** 2)
    return 1.0 - np.sum((y_true - y_pred) ** 2) / denom if denom > 0 else 0.0


def main():
    print('=' * 60)
    print('PGNN-LSTM Evaluation')
    print('=' * 60)

    ckpt_path = os.path.join(ARTIFACTS, 'pgnn_lstm_best.pt')
    if not os.path.exists(ckpt_path):
        print(f'ERROR: {ckpt_path} not found — training not complete yet')
        return 1

    # ── load model ────────────────────────────────────────────────────────────
    print('\n1. Loading model …')
    model = PGNN_LSTM()
    ckpt  = torch.load(ckpt_path, map_location='cpu')
    model.load_state_dict(ckpt['model_state'])
    model.eval()
    print(f'   ✓ Loaded checkpoint from epoch {ckpt["epoch"]}')
    print(f'   ✓ Checkpoint val loss: {ckpt["val_loss"]:.6f}')

    # ── load data ─────────────────────────────────────────────────────────────
    print('\n2. Loading test data …')
    with open(f'{ARTIFACTS}/sequences.pkl', 'rb') as f:
        seq = pickle.load(f)
    with open(f'{ARTIFACTS}/graph_cache.pkl', 'rb') as f:
        gc  = pickle.load(f)
    with open(f'{ARTIFACTS}/scalers.pkl', 'rb') as f:
        scalers = pickle.load(f)

    adj_t = gc['adj']; nf_t = gc['node_feat']
    te_X  = seq['test_X']; te_y  = seq['test_y']
    te_wi = seq['test_wi']; te_geo = seq['test_geo']

    # Rebuild idx→well_id reverse map
    well_to_idx = gc['well_to_idx']
    idx_to_well = {v: k for k, v in well_to_idx.items()}

    print(f'   Test sequences: {len(te_X):,}')

    # ── predict in batches ────────────────────────────────────────────────────
    print('\n3. Running predictions …')
    BATCH = 256
    all_pred = []
    all_true = []

    with torch.no_grad():
        g_embed = model.gcn_embed(nf_t, adj_t)
        for s in range(0, len(te_X), BATCH):
            xb  = te_X[s:s+BATCH]
            wi  = te_wi[s:s+BATCH]
            geo = [te_geo[i] for i in range(s, min(s+BATCH, len(te_X)))]
            sp  = g_embed[wi].unsqueeze(1).expand(-1, PGNN_LSTM.SEQ_LEN, -1)
            x   = torch.cat([xb, sp], dim=-1)
            out = torch.zeros(xb.shape[0], PGNN_LSTM.SEQ_LEN, PGNN_LSTM.LSTM_H)
            grp = {}
            for i, g_ in enumerate(geo): grp.setdefault(g_, []).append(i)
            for g_, idx in grp.items(): out[idx] = model._lstm(g_)(x[idx])
            a, _ = model.attn(out, out, out); out = model.anorm(out + a)
            pred = model.fc2(model.relu(model.fc1(model.drop(out[:, -1, :]))))
            all_pred.append(pred.numpy())
            all_true.append(te_y[s:s+BATCH].numpy())

    pred_arr = np.vstack(all_pred)   # [N_test, 12]
    true_arr = np.vstack(all_true)

    print(f'   Predictions shape: {pred_arr.shape}')

    # ── per-well metrics (first step-ahead only for simplicity) ──────────────
    print('\n4. Computing per-well metrics (step-1 forecast) …')

    # Group test indices by well
    well_records = {}
    for i in range(len(te_wi)):
        wid = idx_to_well.get(int(te_wi[i]), f'well_{te_wi[i]}')
        if wid not in well_records:
            well_records[wid] = {'pred': [], 'true': [], 'geo': te_geo[i]}
        sc = scalers.get(wid)
        if sc is None:
            continue
        # Inverse-transform first step of each sequence
        p = float(sc.inverse_transform([[pred_arr[i, 0]]])[0, 0])
        t = float(sc.inverse_transform([[true_arr[i, 0]]])[0, 0])
        well_records[wid]['pred'].append(p)
        well_records[wid]['true'].append(t)

    rows = []
    for wid, rec in well_records.items():
        if len(rec['pred']) < 5:
            continue
        yt = np.array(rec['true'])
        yp = np.array(rec['pred'])
        # Skip wells with near-zero variance (degenerate R²/NSE)
        if np.std(yt) < 0.05:
            continue
        rmse = np.sqrt(mean_squared_error(yt, yp))
        mae  = mean_absolute_error(yt, yp)
        r2   = r2_score(yt, yp)
        nse_ = nse(yt, yp)
        # Clip R²/NSE to [-1, 1] for display (avoid display explosion)
        r2   = float(np.clip(r2,   -1.0, 1.0))
        nse_ = float(np.clip(nse_, -1.0, 1.0))
        rows.append({
            'well_id':  wid,
            'geology':  rec['geo'],
            'n_test':   len(yt),
            'rmse_m':   round(rmse, 3),
            'mae_m':    round(mae,  3),
            'r2':       round(r2,   3),
            'nse':      round(nse_, 3),
        })

    results_df = pd.DataFrame(rows).sort_values('rmse_m')

    # ── print summary ─────────────────────────────────────────────────────────
    print()
    print(f"  {'Well':<18} {'Geology':<12} {'N':>5} {'RMSE':>7} {'MAE':>7} {'R²':>6} {'NSE':>6}")
    print('  ' + '─' * 65)
    for _, r in results_df.head(20).iterrows():
        print(f"  {r['well_id']:<18} {r['geology']:<12} {r['n_test']:>5}"
              f"  {r['rmse_m']:>6.3f}  {r['mae_m']:>6.3f}  {r['r2']:>5.3f}  {r['nse']:>5.3f}")
    print('  ' + '─' * 65)

    mean_row = results_df[['rmse_m','mae_m','r2','nse']].mean()
    print(f"\n  Overall mean  RMSE={mean_row['rmse_m']:.3f} m  "
          f"MAE={mean_row['mae_m']:.3f} m  R²={mean_row['r2']:.3f}  NSE={mean_row['nse']:.3f}")

    print(f"\n  By geology type:")
    for geo in results_df['geology'].unique():
        sub = results_df[results_df['geology'] == geo]
        print(f"    {geo:<12} N={len(sub):>3}  "
              f"RMSE={sub['rmse_m'].mean():.3f}  "
              f"R²={sub['r2'].mean():.3f}  "
              f"NSE={sub['nse'].mean():.3f}")

    # ── save ──────────────────────────────────────────────────────────────────
    out_csv  = f'{ARTIFACTS}/evaluation_results.csv'
    out_json = f'{ARTIFACTS}/evaluation_summary.json'

    results_df.to_csv(out_csv, index=False)

    summary = {
        'n_wells_evaluated': len(results_df),
        'mean_rmse_m':  float(mean_row['rmse_m']),
        'mean_mae_m':   float(mean_row['mae_m']),
        'mean_r2':      float(mean_row['r2']),
        'mean_nse':     float(mean_row['nse']),
        'by_geology': {
            geo: {
                'n': int(len(results_df[results_df['geology']==geo])),
                'rmse': float(results_df[results_df['geology']==geo]['rmse_m'].mean()),
                'r2':   float(results_df[results_df['geology']==geo]['r2'].mean()),
                'nse':  float(results_df[results_df['geology']==geo]['nse'].mean()),
            }
            for geo in results_df['geology'].unique()
        }
    }
    with open(out_json, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f'\n  ✓ Results → {out_csv}')
    print(f'  ✓ Summary → {out_json}')
    print('=' * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
