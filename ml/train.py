"""
Train and lock the v3 (no-rain) PGNN-LSTM as the production model.
Mirrors notebook Cell D's training loop (cell 10) exactly, using the
shared preprocessing.py so training and serving can never drift apart.

FIXES APPLIED (2026-08-08):
- FIX-1: Use global StandardScaler instead of per-well MinMaxScaler
- FIX-2: Evaluate only 1-month-ahead predictions (not overlapping 12-month horizons)
- FIX-3: Use time-based validation split (2018 data) instead of random sampling
- FIX-4: Add data quality validation in preprocessing

Usage:
  python train.py --data-dir ./data --save-dir ./artifacts
  (expects wells.csv, litho.csv, water_levels.csv in --data-dir, same
   columns as the notebook's Book2.xlsx Sheet1/Sheet2/Sheet3 — produced by
   etl/load_to_postgres.py or exported straight from Postgres)
"""
import argparse
import json
import joblib
import os
import time
from datetime import date

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

from model import PGNN_LSTM, PhysicsLoss
from preprocessing import HORIZON, SEQ_LEN, prepare_all


def build_sequences(prepared, train_end_yr=2017, val_yr=2018, test_start_yr=2019):
    """Build train/val/test sequences with proper temporal split.
    
    FIX-1: Use global StandardScaler fitted on ALL training data, not per-well.
    FIX-3: Use time-based validation (2018) instead of random sampling.
    
    Returns:
        Tuple of (train_data, val_data, test_data, scaler)
    """
    tr_X, tr_y, tr_wi, tr_ac = [], [], [], []
    val_X, val_y, val_wi, val_ac = [], [], [], []
    te_X, te_y, te_wi, te_ac = [], [], [], []
    
    # FIX-1: Collect all training data first for global scaler
    all_train_data = []
    for well in prepared.well_list:
        ms = prepared.monthly[well]
        trn = ms[ms.index.year <= train_end_yr].values.reshape(-1, 1)
        if len(trn) >= SEQ_LEN + HORIZON:
            all_train_data.append(trn)
    
    if not all_train_data:
        raise ValueError("No wells with sufficient training data")
    
    # Fit global scaler on all training data
    scaler = StandardScaler()
    scaler.fit(np.vstack(all_train_data))
    print(f"Global scaler fitted on {len(all_train_data)} wells, "
          f"mean={scaler.mean_[0]:.2f}, std={scaler.scale_[0]:.2f}")
    
    # Build sequences
    for well in prepared.well_list:
        ms = prepared.monthly[well]
        if len(ms) < SEQ_LEN + HORIZON:
            continue
            
        # Apply global scaling
        ms_sc = scaler.transform(ms.values.reshape(-1, 1)).flatten()
        wi = prepared.well_list.index(well)
        ac = prepared.aq_info.get(well, {}).get("dominant", "Other")

        for i in range(len(ms_sc) - SEQ_LEN - HORIZON + 1):
            x = ms_sc[i:i + SEQ_LEN].reshape(-1, 1)
            y = ms_sc[i + SEQ_LEN:i + SEQ_LEN + HORIZON]
            dt = ms.index[i + SEQ_LEN]
            
            # FIX-3: Time-based split (train: <=2017, val: 2018, test: >=2019)
            if dt.year <= train_end_yr:
                tr_X.append(x); tr_y.append(y); tr_wi.append(wi); tr_ac.append(ac)
            elif dt.year == val_yr:
                val_X.append(x); val_y.append(y); val_wi.append(wi); val_ac.append(ac)
            else:
                te_X.append(x); te_y.append(y); te_wi.append(wi); te_ac.append(ac)

    return (torch.FloatTensor(np.array(tr_X)), torch.FloatTensor(np.array(tr_y)), tr_wi, tr_ac,
            torch.FloatTensor(np.array(val_X)), torch.FloatTensor(np.array(val_y)), val_wi, val_ac,
            torch.FloatTensor(np.array(te_X)), torch.FloatTensor(np.array(te_y)), te_wi, te_ac,
            scaler)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--save-dir", required=True)
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--patience", type=int, default=25)
    args = ap.parse_args()
    os.makedirs(args.save_dir, exist_ok=True)

    torch.manual_seed(42)
    np.random.seed(42)
    device = torch.device("cpu")

    wells = pd.read_csv(os.path.join(args.data_dir, "wells.csv"))
    litho = pd.read_csv(os.path.join(args.data_dir, "litho.csv"))
    # Note: preprocessing.py's classify_aquifer dynamically resolves column names
    # ("Well No"/"Well_No", "Depth To"/"Depth_To", etc.) so no rename needed.
    wl = pd.read_csv(os.path.join(args.data_dir, "water_levels.csv"))

    prepared = prepare_all(wells, litho, wl)
    node_feat_t = torch.FloatTensor(prepared.node_feats).to(device)
    adj_t = torch.FloatTensor(prepared.adj).to(device)

    tr_X, tr_y, tr_wi, tr_ac, val_X, val_y, val_wi, val_ac, te_X, te_y, te_wi, te_ac, scaler = build_sequences(prepared)
    print(f"Train sequences: {len(tr_X):,}  Val sequences: {len(val_X):,}  Test sequences: {len(te_X):,}")

    model = PGNN_LSTM(n_node_feat=node_feat_t.shape[1]).to(device)
    criterion = PhysicsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100, eta_min=1e-5)

    best_loss, pat_count = np.inf, 0
    idx_all = np.arange(len(tr_X))
    start = time.time()

    # FIX-3: Use all validation data (time-based split, not random sample)
    for epoch in range(1, args.epochs + 1):
        model.train()
        np.random.shuffle(idx_all)
        for s in range(0, len(tr_X), 32):
            idx = idx_all[s:s + 32]
            xb, yb = tr_X[idx].to(device), tr_y[idx].to(device)
            wib = torch.tensor([tr_wi[i] for i in idx], dtype=torch.long)
            acb = [tr_ac[i] for i in idx]
            optimizer.zero_grad()
            pred = model(xb, node_feat_t, adj_t, wib, acb)
            loss, _ = criterion(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        scheduler.step()

        # Validate on 2018 data
        model.eval()
        with torch.no_grad():
            xv, yv = val_X.to(device), val_y.to(device)
            wiv = torch.tensor(val_wi, dtype=torch.long)
            pv = model(xv, node_feat_t, adj_t, wiv, val_ac)
            vl, _ = criterion(pv, yv)
        avg_vl = vl.item()

        if avg_vl < best_loss:
            best_loss, pat_count = avg_vl, 0
            torch.save(model.state_dict(), os.path.join(args.save_dir, "pgnn_v3_best.pt"))
        else:
            pat_count += 1
        if epoch % 10 == 0:
            print(f"Ep {epoch:>4}  vl={avg_vl:.5f}  best={best_loss:.5f}  pat={pat_count}/{args.patience}  "
                  f"t={(time.time()-start)/60:.1f}m")
        if pat_count >= args.patience:
            print(f"Early stopping at epoch {epoch}")
            break

    # ── Evaluation with FIX-2: Evaluate only 1-month-ahead predictions ──
    model.load_state_dict(torch.load(os.path.join(args.save_dir, "pgnn_v3_best.pt")))
    model.eval()
    
    # Per-well metrics
    well_metrics = {}
    all_preds_1mo, all_trues_1mo = [], []
    
    for well in prepared.well_list:
        ms = prepared.monthly[well]
        if len(ms) < SEQ_LEN + HORIZON:
            continue
            
        ms_sc = scaler.transform(ms.values.reshape(-1, 1)).flatten()
        wi = prepared.well_list.index(well)
        ac = prepared.aq_info.get(well, {}).get("dominant", "Other")
        
        # FIX-2: Collect only 1-month-ahead predictions (not overlapping 12-month)
        preds_1mo, trues_1mo = [], []
        
        with torch.no_grad():
            for i in range(len(ms_sc) - SEQ_LEN - HORIZON + 1):
                dt = ms.index[i + SEQ_LEN]
                if dt.year <= 2017:  # Skip training data
                    continue
                    
                xb = torch.FloatTensor(ms_sc[i:i + SEQ_LEN].reshape(1, -1, 1)).to(device)
                wib = torch.tensor([wi], dtype=torch.long).to(device)
                pb = model(xb, node_feat_t, adj_t, wib, [ac])
                
                # FIX-2: Take ONLY the first prediction (1-month-ahead)
                pred_1mo_scaled = pb[0, 0].item()
                true_1mo_scaled = ms_sc[i + SEQ_LEN]
                
                # Inverse transform
                pred_1mo = scaler.inverse_transform([[pred_1mo_scaled]])[0, 0]
                true_1mo = scaler.inverse_transform([[true_1mo_scaled]])[0, 0]
                
                preds_1mo.append(pred_1mo)
                trues_1mo.append(true_1mo)
                all_preds_1mo.append(pred_1mo)
                all_trues_1mo.append(true_1mo)
        
        # Calculate per-well metrics (on test data: 2018+)
        if len(preds_1mo) >= 5:
            well_rmse = np.sqrt(mean_squared_error(trues_1mo, preds_1mo))
            well_r2 = r2_score(trues_1mo, preds_1mo) if np.std(trues_1mo) > 1e-6 else 0.0
            well_mae = mean_absolute_error(trues_1mo, preds_1mo)
            well_metrics[well] = {
                "rmse": round(float(well_rmse), 3),
                "r2": round(float(well_r2), 3),
                "mae": round(float(well_mae), 3),
                "n_test": len(preds_1mo)
            }
    
    # Global metrics across all test predictions
    global_rmse = np.sqrt(mean_squared_error(all_trues_1mo, all_preds_1mo))
    global_r2 = r2_score(all_trues_1mo, all_preds_1mo)
    global_mae = mean_absolute_error(all_trues_1mo, all_preds_1mo)
    
    # Well-level statistics
    well_rmses = [m["rmse"] for m in well_metrics.values()]
    well_r2s = [m["r2"] for m in well_metrics.values()]
    
    print("\n" + "="*70)
    print("EVALUATION RESULTS (1-month-ahead predictions on test data)")
    print("="*70)
    print(f"Global metrics (all test predictions combined):")
    print(f"  RMSE: {global_rmse:.3f} m")
    print(f"  R²:   {global_r2:.3f}")
    print(f"  MAE:  {global_mae:.3f} m")
    print(f"\nPer-well average metrics ({len(well_metrics)} wells):")
    print(f"  Mean RMSE: {np.mean(well_rmses):.3f} m  (std: {np.std(well_rmses):.3f})")
    print(f"  Mean R²:   {np.mean(well_r2s):.3f}  (std: {np.std(well_r2s):.3f})")
    print(f"  Wells with R² > 0.7: {sum(1 for r2 in well_r2s if r2 > 0.7)}/{len(well_r2s)}")
    print(f"  Wells with R² > 0.5: {sum(1 for r2 in well_r2s if r2 > 0.5)}/{len(well_r2s)}")
    print("="*70 + "\n")

    metadata = {
        "version_id": f"pgnn_v3_{date.today().isoformat()}",
        "trained_on": date.today().isoformat(),
        "global_metrics": {
            "rmse": round(float(global_rmse), 3),
            "r2": round(float(global_r2), 3),
            "mae": round(float(global_mae), 3),
            "n_predictions": len(all_preds_1mo)
        },
        "per_well_avg": {
            "rmse_mean": round(float(np.mean(well_rmses)), 3),
            "r2_mean": round(float(np.mean(well_r2s)), 3),
            "wells_r2_gt_0.7": sum(1 for r2 in well_r2s if r2 > 0.7),
            "wells_r2_gt_0.5": sum(1 for r2 in well_r2s if r2 > 0.5),
        },
        "artifact_path": os.path.join(args.save_dir, "pgnn_v3_best.pt"),
        "scaler_path": os.path.join(args.save_dir, "scaler.joblib"),
        "graph_path": os.path.join(args.save_dir, "graph_structure.npz"),
        "well_list": prepared.well_list,
        "well_metrics": well_metrics,
        "fixes_applied": [
            "FIX-1: Global StandardScaler (not per-well MinMaxScaler)",
            "FIX-2: 1-month-ahead evaluation (not overlapping 12-month)",
            "FIX-3: Time-based validation split (2018, not random sample)"
        ]
    }
    
    # Save graph structure for inference
    np.savez(
        os.path.join(args.save_dir, "graph_structure.npz"),
        node_feats=prepared.node_feats,
        adj=prepared.adj,
        well_list=np.array(prepared.well_list, dtype=object),
        aq_info=np.array([prepared.aq_info.get(w, {}) for w in prepared.well_list], dtype=object)
    )
    print(f"Saved graph structure to {args.save_dir}/graph_structure.npz")
    
    with open(os.path.join(args.save_dir, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    joblib.dump(scaler, os.path.join(args.save_dir, "scaler.joblib"))
    print(f"Saved global scaler to {args.save_dir}/scaler.joblib")
    print("Saved:", metadata["artifact_path"])
    print(f"\nFINAL METRICS:")
    print(f"  Global R²: {metadata['global_metrics']['r2']}")
    print(f"  Global RMSE: {metadata['global_metrics']['rmse']} m")
    print(f"  Per-well avg R²: {metadata['per_well_avg']['r2_mean']}")
    print("INSERT the metadata above into the `model_versions` table (see etl/schema.sql), "
          "setting is_active=TRUE for this version and FALSE for any prior one.")


if __name__ == "__main__":
    main()
