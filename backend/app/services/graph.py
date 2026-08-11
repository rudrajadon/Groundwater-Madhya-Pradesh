"""
Dynamic graph extension for arbitrary GPS points not in the trained
52-well graph. Reuses the exact edge-scoring rule from ml/preprocessing.py
(edge_weight) so an inserted point is scored identically to how the model
was trained to interpret distances/geology/block matches.

GCN weights are shared across nodes by construction (see ml/model.py
GraphConv), so no retraining is needed to score a new point — we just
compute its row of the adjacency matrix and run one extra forward pass.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml"))
from preprocessing import DIST_THR, edge_weight  # noqa: E402

NEAREST_WELL_SNAP_KM = 2.0


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def find_nearest_well(lat, lon, wells: list[dict]) -> tuple[dict, float]:
    """wells: list of {well_id, lat, lon, ...}. Returns (nearest_well, dist_km)."""
    best, best_d = None, float("inf")
    for w in wells:
        d = haversine_km(lat, lon, w["lat"], w["lon"])
        if d < best_d:
            best, best_d = w, d
    return best, best_d


def resolve_query_point(lat, lon, wells: list[dict]) -> dict:
    """Decision from project plan Section 4.3/4.5:
    - within NEAREST_WELL_SNAP_KM of an existing well -> use that well's node directly
    - otherwise -> caller must build an extended adjacency row via
      build_extended_edges() and run inference with the enlarged graph
    """
    nearest, dist_km = find_nearest_well(lat, lon, wells)
    if nearest is None:
        raise ValueError("No wells available to match against")
    return {
        "matched_existing_well": dist_km <= NEAREST_WELL_SNAP_KM,
        "well": nearest,
        "distance_km": round(dist_km, 3),
    }


def build_extended_edges(point_coord, point_zone, point_block, existing_wells: list[dict]) -> np.ndarray:
    """Compute edge weights from a new point to all existing wells.
    Uses (lon, lat) as coordinate pairs since edge_weight expects (easting, northing) ~ (lon, lat)."""
    return np.array([
        edge_weight(point_coord, (w["lon"], w["lat"]), point_zone,
                    w["aquifer_zone"], point_block, w.get("block", ""))
        for w in existing_wells
    ])
