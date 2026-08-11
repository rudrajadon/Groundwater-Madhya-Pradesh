"""
Load exported CSVs (from export_mdb.sh) into PostgreSQL/PostGIS.

Run AFTER:
  1. etl/export_mdb.sh has produced CSVs in ./raw_csv/
  2. You've inspected ./raw_csv/_table_list.txt and confirmed the real
     table names (see TABLE_NAME_MAP below — placeholders until then)
  3. etl/schema.sql has been applied to your database

Usage:
  export DATABASE_URL=postgresql://user:pass@localhost:5432/groundwater
  python load_to_postgres.py --csv-dir ./raw_csv
"""
import argparse
import os
import sys

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from parse_coordinates import parse_and_validate

# ── EDIT THIS after running export_mdb.sh and checking real table names ──
# Left side = logical role, right side = CSV filename (without .csv) as it
# appears after export_mdb.sh's `tr ' /' '__'` sanitization.
TABLE_NAME_MAP = {
    "wells": "GroundWater-General",
    "readings": "Water_Levels",
    "lithology": "Well_Lithology",
    "rainfall_stations": "Master_-_Rainfall_Station",
    "rainfall_readings": "Data-Rainfall",
}

WELL_COLUMN_MAP = {
    # logical column -> likely source column name (verify against your CSV
    # header row — mdb-tools preserves the Access field names as-is)
    "well_id": "Well No",
    "well_type": "Well use",
    "agency": "Agency",
    "district": "District",
    "tahsil": "Tahsil / Taluk",
    "block": "Block / Mandal",
    "village": "Village",
    "lat_raw": "Latitude",
    "lon_raw": "Longitude",
    "elevation_m": "Elevation of Ground Level",
    "command_area": "Command Area",
}


def load_wells(conn, csv_dir: str):
    path = os.path.join(csv_dir, f"{TABLE_NAME_MAP['wells']}.csv")
    if not os.path.exists(path):
        print(f"[skip] wells CSV not found at {path} — update TABLE_NAME_MAP", file=sys.stderr)
        return
    df = pd.read_csv(path)
    rows = []
    n_invalid = 0
    for _, r in df.iterrows():
        well_id = str(r.get(WELL_COLUMN_MAP["well_id"], "")).strip()
        if not well_id or well_id.lower() == "nan":
            continue
        lat_raw = str(r.get(WELL_COLUMN_MAP["lat_raw"], "") or "")
        lon_raw = str(r.get(WELL_COLUMN_MAP["lon_raw"], "") or "")
        coord = parse_and_validate(lat_raw, lon_raw)
        if not coord.valid:
            n_invalid += 1
        rows.append((
            well_id,
            r.get(WELL_COLUMN_MAP["well_type"]),
            r.get(WELL_COLUMN_MAP["agency"]),
            r.get(WELL_COLUMN_MAP["district"]),
            r.get(WELL_COLUMN_MAP["tahsil"]),
            r.get(WELL_COLUMN_MAP["block"]),
            r.get(WELL_COLUMN_MAP["village"]),
            coord.lon, coord.lat,          # ST_MakePoint takes (lon, lat)
            lat_raw, lon_raw,
            coord.valid,
            r.get(WELL_COLUMN_MAP["elevation_m"]),
            r.get(WELL_COLUMN_MAP["command_area"]),
        ))

    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO wells (well_id, well_type, agency, district, tahsil,
                block, village, geom, lat_raw, lon_raw, coord_validated,
                elevation_m, command_area)
            VALUES %s
            ON CONFLICT (well_id) DO UPDATE SET
                geom = EXCLUDED.geom,
                coord_validated = EXCLUDED.coord_validated
        """, rows, template="""(
            %s, %s, %s, %s, %s, %s, %s,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
            %s, %s, %s, %s, %s
        )""")
    conn.commit()
    print(f"Loaded {len(rows)} wells ({n_invalid} with unvalidated/suspect coordinates — "
          f"check them manually before relying on the map view).")


def load_readings(conn, csv_dir: str):
    path = os.path.join(csv_dir, f"{TABLE_NAME_MAP['readings']}.csv")
    if not os.path.exists(path):
        print(f"[skip] readings CSV not found at {path} — update TABLE_NAME_MAP", file=sys.stderr)
        return
    df = pd.read_csv(path)
    # Map actual CSV columns to expected names
    date_col = "date" if "date" in df.columns else "Date"
    well_col = "Well No" if "Well No" in df.columns else "WellNo"
    depth_col = "Water Level" if "Water Level" in df.columns else "PW-SWL"
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    # Elevation lookup for head_msl computation
    with conn.cursor() as cur:
        cur.execute("SELECT well_id, elevation_m FROM wells")
        elev = dict(cur.fetchall())

    rows = []
    for _, r in df.iterrows():
        well_id = str(r.get(well_col, "")).strip()
        depth = r.get(depth_col)
        if not well_id or pd.isna(depth):
            continue
        e = elev.get(well_id)
        head_msl = (float(e) - float(depth)) if e is not None else None
        rows.append((well_id, r[date_col].date(), float(depth), head_msl, "mdb_import"))

    # Deduplicate: keep last occurrence for each (well_id, date) pair
    # because Postgres ON CONFLICT can't handle duplicates within the same batch
    seen = {}
    for row in rows:
        seen[(row[0], row[1])] = row
    rows = list(seen.values())
    print(f"Deduplicated to {len(rows)} unique (well, date) readings.")

    with conn.cursor() as cur:
        execute_values(cur, """
            INSERT INTO readings (well_id, date, depth_bgl_m, head_msl_m, source)
            VALUES %s
            ON CONFLICT (well_id, date) DO UPDATE SET
                depth_bgl_m = EXCLUDED.depth_bgl_m,
                head_msl_m = EXCLUDED.head_msl_m
        """, rows)
    conn.commit()
    print(f"Loaded {len(rows)} water-level readings.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv-dir", required=True)
    args = ap.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("Set DATABASE_URL env var, e.g. postgresql://user:pass@localhost/groundwater")

    conn = psycopg2.connect(db_url)
    load_wells(conn, args.csv_dir)
    load_readings(conn, args.csv_dir)
    conn.close()


if __name__ == "__main__":
    main()
