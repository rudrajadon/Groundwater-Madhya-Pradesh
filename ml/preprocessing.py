"""
Shared preprocessing for PGNN-LSTM — used by BOTH training (train.py) and
serving (inference.py) so they can never silently drift apart, unlike the
original notebook where Book2.xlsx and the mdb had no documented link.

Extracted directly from PGNN_LSTM_Final_ReviewerCorrected.ipynb, Cell D
(cell 10): BGL->MSL conversion, joint lithology+depth aquifer classification,
geology-informed graph construction, node feature engineering.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

DIST_THR = 0.15   # ~15 km, same as source notebook
SEQ_LEN = 24
HORIZON = 12


def bgl_to_msl(wl: pd.DataFrame, wells: pd.DataFrame) -> pd.DataFrame:
    """[FIX-1 from notebook] Convert depth-BGL to hydraulic head (m MSL)."""
    wl = wl.copy()
    wl["Elevation of Ground Level"] = pd.to_numeric(
        wl["Elevation of Ground Level"], errors="coerce"
    )
    block_median_elev = (
        wl.dropna(subset=["Elevation of Ground Level"])
        .groupby("Block / Mandal")["Elevation of Ground Level"].median()
    )

    def fill_elev(row):
        if pd.notna(row["Elevation of Ground Level"]):
            return row["Elevation of Ground Level"]
        return block_median_elev.get(row["Block / Mandal"], 530.0)

    wl["Elevation of Ground Level"] = wl.apply(fill_elev, axis=1)
    wl["depth_bgl"] = wl["Water Level"].copy()
    wl["head_msl"] = wl["Elevation of Ground Level"] - wl["Water Level"]
    wl["Water Level"] = wl["head_msl"]
    return wl


def classify_aquifer(well_no: str, litho_df: pd.DataFrame):
    """[FIX-2 from notebook] Joint lithology-keyword + depth-interval rule
    (Singhal & Gupta, 2010): 0-15m Weathered, 15-40m Massive, >40m Fractured,
    lithology keyword wins when decisive."""
    # Support both "Well_No" and "Well No" column naming conventions
    well_col = "Well_No" if "Well_No" in litho_df.columns else "Well No"
    depth_col = "Depth_To" if "Depth_To" in litho_df.columns else "Depth To"
    lith_col = "Lithology" if "Lithology" in litho_df.columns else "lithology"
    wdf = litho_df[litho_df[well_col] == well_no]
    wdf = wdf[wdf[depth_col] < 200].sort_values(depth_col)
    if len(wdf) == 0:
        return "Other", 0.0, 0.0, 0.0

    prev = 0.0
    thick = {"Weathered": 0.0, "Fractured": 0.0, "Massive": 0.0, "Other": 0.0}
    for _, row in wdf.iterrows():
        t = row[depth_col] - prev
        l = str(row[lith_col]).lower()
        depth_mid = (prev + row[depth_col]) / 2.0

        if any(x in l for x in ["weathered", "highly weathered", "laterit", "soil", "regolith"]):
            lith_class = "Weathered"
        elif any(x in l for x in ["fractured", "jointed", "vesicular", "brecciat"]):
            lith_class = "Fractured"
        elif any(x in l for x in ["hard", "massive", "compact", "dense", "fresh"]):
            lith_class = "Massive"
        else:
            lith_class = None

        if depth_mid <= 15.0:
            depth_class = "Weathered"
        elif depth_mid <= 40.0:
            depth_class = "Massive"
        else:
            depth_class = "Fractured"

        final_class = lith_class if lith_class else depth_class
        thick[final_class] += t
        prev = row[depth_col]

    total = sum(thick.values())
    if total == 0:
        return "Other", 0.0, 0.0, 0.0
    dom = max(["Weathered", "Fractured", "Massive"], key=lambda k: thick[k])
    return (dom, round(thick["Weathered"] / total * 100, 1),
            round(thick["Fractured"] / total * 100, 1),
            round(thick["Massive"] / total * 100, 1))


def build_monthly_series(wl: pd.DataFrame) -> dict:
    monthly = {}
    for well in sorted(wl["Well No"].unique()):
        wdf = wl[wl["Well No"] == well].set_index("date")
        ms = wdf["Water Level"].resample("MS").mean()
        ms = ms.interpolate(method="linear", limit=3).dropna()
        if len(ms) >= 60:
            monthly[well] = ms
    return monthly


def build_graph(well_list: list, wells: pd.DataFrame, aq_info: dict) -> np.ndarray:
    """Geology-informed adjacency matrix — identical rule used at train and
    serve time, including for a NEW point not in well_list (see
    backend/app/services/graph.py::extend_adjacency, which reuses this
    exact scoring logic for dynamic node insertion)."""
    n = len(well_list)
    coords = {}
    for w in well_list:
        row = wells[wells["Well No"] == w]
        coords[w] = (
            float(row["Easting"].values[0]) if len(row) else 75.6,
            float(row["Northing"].values[0]) if len(row) else 22.8,
        )
    adj = np.zeros((n, n))
    for i, w1 in enumerate(well_list):
        for j, w2 in enumerate(well_list):
            if i == j:
                continue
            dx = coords[w1][0] - coords[w2][0]
            dy = coords[w1][1] - coords[w2][1]
            d = np.sqrt(dx**2 + dy**2)
            if d < DIST_THR:
                geol_match = aq_info.get(w1, {}).get("dominant") == aq_info.get(w2, {}).get("dominant")
                geol_score = 1.0 if geol_match else 0.4
                r1 = wells[wells["Well No"] == w1]["Block / Mandal"]
                r2 = wells[wells["Well No"] == w2]["Block / Mandal"]
                blk_score = 1.0
                if len(r1) and len(r2) and r1.values[0] != r2.values[0]:
                    blk_score = 0.6
                adj[i, j] = (1 - d / DIST_THR) * geol_score * blk_score
    return adj


def edge_weight(coord_a, coord_b, zone_a, zone_b, block_a, block_b) -> float:
    """The single-edge version of build_graph's scoring rule — used by the
    backend to compute edges for a brand-new lat/lon point at request time
    without needing to rebuild the whole matrix."""
    dx, dy = coord_a[0] - coord_b[0], coord_a[1] - coord_b[1]
    d = np.sqrt(dx**2 + dy**2)
    if d >= DIST_THR:
        return 0.0
    geol_score = 1.0 if zone_a == zone_b else 0.4
    blk_score = 1.0 if block_a == block_b else 0.6
    return (1 - d / DIST_THR) * geol_score * blk_score


def build_node_features(well_list: list, wells: pd.DataFrame, monthly: dict, aq_info: dict) -> np.ndarray:
    wells = wells.copy()
    wells["Command Area"] = pd.to_numeric(wells["Command Area"], errors="coerce").fillna(0.0)
    dist_elev_median = pd.to_numeric(wells["Elevation of Ground Level"], errors="coerce").median()
    wells["Elevation of Ground Level"] = pd.to_numeric(
        wells["Elevation of Ground Level"], errors="coerce"
    ).fillna(dist_elev_median)

    feats = []
    for w in well_list:
        row = wells[wells["Well No"] == w]
        elev = float(row["Elevation of Ground Level"].values[0]) if len(row) else dist_elev_median
        cmd = float(row["Command Area"].values[0]) if len(row) else 0.0
        ms = monthly[w].values
        sl, *_ = sp_stats.linregress(np.arange(len(ms)), ms)
        sl = 0.0 if (np.isnan(sl) or np.isinf(sl)) else sl
        aq = aq_info.get(w, {})
        feats.append([
            elev / 600.0, cmd, float(np.mean(ms)) / 530.0, float(np.std(ms)) / 15.0,
            float(sl) * 10.0,
            1.0 if aq.get("dominant") == "Weathered" else 0.0,
            1.0 if aq.get("dominant") == "Fractured" else 0.0,
            1.0 if aq.get("dominant") == "Massive" else 0.0,
        ])
    nf = np.array(feats, dtype=np.float32)
    for c in range(nf.shape[1]):
        col = nf[:, c]
        if np.isnan(col).any():
            nf[np.isnan(col), c] = np.nanmedian(col)
    return nf


@dataclass
class PreparedData:
    well_list: list
    monthly: dict
    aq_info: dict
    adj: np.ndarray
    node_feats: np.ndarray
    wells: pd.DataFrame = field(repr=False)


def prepare_all(wells: pd.DataFrame, litho: pd.DataFrame, wl: pd.DataFrame) -> PreparedData:
    """End-to-end: mirrors notebook Cell D exactly (v3 / no-rain path).
    
    FIX-4: Added data quality validation and reporting.
    """
    print("\n" + "="*70)
    print("DATA QUALITY VALIDATION")
    print("="*70)
    
    # Original counts
    n_wells_orig = wells["Well No"].nunique()
    n_readings_orig = len(wl)
    
    wl = wl.copy()
    wl["date"] = pd.to_datetime(wl["date"], format="%m/%d/%y %H:%M:%S", errors="coerce")
    
    # Count parsing failures
    n_date_invalid = wl["date"].isna().sum()
    if n_date_invalid > 0:
        print(f"⚠ Date parsing: {n_date_invalid}/{n_readings_orig} readings have invalid dates (dropped)")
    
    wl = wl.dropna(subset=["date", "Water Level"])
    
    # Check for extreme values
    extreme_readings = wl[wl["Water Level"] > 60]
    if len(extreme_readings) > 0:
        print(f"⚠ Extreme values: {len(extreme_readings)} readings with depth > 60m BGL (dropped)")
        print(f"  Wells affected: {extreme_readings['Well No'].unique()[:5].tolist()}")
    
    wl = wl[wl["Water Level"] <= 60].copy()
    wl = wl.sort_values(["Well No", "date"]).reset_index(drop=True)
    
    # Check for missing elevation data
    wl = wl.merge(
        wells[["Well No", "Elevation of Ground Level", "Block / Mandal", "Command Area", "Easting", "Northing"]],
        on="Well No", how="left",
    )
    
    n_missing_elev = wl["Elevation of Ground Level"].isna().sum()
    if n_missing_elev > 0:
        print(f"⚠ Missing elevation: {n_missing_elev} readings lack elevation data")
        print(f"  Will use block median or default (530m)")
    
    # Check coordinate validity (Madhya Pradesh bounds: 21-27°N, 74-83°E)
    wells_with_coords = wells.dropna(subset=["Easting", "Northing"])
    invalid_coords = wells_with_coords[
        (wells_with_coords["Easting"] < 74.0) | (wells_with_coords["Easting"] > 83.0) |
        (wells_with_coords["Northing"] < 21.0) | (wells_with_coords["Northing"] > 27.0)
    ]
    if len(invalid_coords) > 0:
        print(f"⚠ Invalid coordinates: {len(invalid_coords)} wells outside Madhya Pradesh bounds")
        print(f"  Wells: {invalid_coords['Well No'].tolist()[:5]}")
    
    wl = bgl_to_msl(wl, wells)

    aq_info = {}
    wells_without_litho = []
    for w in wells["Well No"].unique():
        dom, wp, fp, mp = classify_aquifer(w, litho)
        aq_info[w] = {"dominant": dom, "wthr_pct": wp, "frac_pct": fp, "mass_pct": mp}
        if dom == "Other":
            wells_without_litho.append(w)
    
    if wells_without_litho:
        print(f"⚠ Missing lithology: {len(wells_without_litho)} wells lack lithology logs")
        print(f"  Classified as 'Other': {wells_without_litho[:5]}")

    monthly = build_monthly_series(wl)
    well_list = sorted(monthly.keys())
    
    n_wells_final = len(well_list)
    n_readings_final = sum(len(monthly[w]) for w in well_list)
    
    print(f"\n✓ Final dataset:")
    print(f"  Wells: {n_wells_final} (started with {n_wells_orig})")
    print(f"  Monthly observations: {n_readings_final}")
    print(f"  Date range: {min(monthly[w].index[0] for w in well_list).strftime('%Y-%m')} to "
          f"{max(monthly[w].index[-1] for w in well_list).strftime('%Y-%m')}")
    print(f"  Aquifer classes: W={sum(1 for w in well_list if aq_info[w]['dominant']=='Weathered')}, "
          f"F={sum(1 for w in well_list if aq_info[w]['dominant']=='Fractured')}, "
          f"M={sum(1 for w in well_list if aq_info[w]['dominant']=='Massive')}, "
          f"O={sum(1 for w in well_list if aq_info[w]['dominant']=='Other')}")
    print("="*70 + "\n")
    
    adj = build_graph(well_list, wells, aq_info)
    node_feats = build_node_features(well_list, wells, monthly, aq_info)

    return PreparedData(well_list, monthly, aq_info, adj, node_feats, wells)
