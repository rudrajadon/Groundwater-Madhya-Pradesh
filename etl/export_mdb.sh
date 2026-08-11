#!/usr/bin/env bash
# Export every user table in IndorePZ.mdb to CSV using mdb-tools.
#
# PREREQUISITE (not available in Claude's sandbox — run this on your own
# machine / CI where you have internet access):
#   Ubuntu/Debian:  sudo apt-get install mdbtools
#   macOS:          brew install mdbtools
#
# Usage:
#   ./export_mdb.sh /path/to/IndorePZ.mdb ./raw_csv
#
# NOTE ON TABLE NAMES: from inspecting IndorePZ.mdb directly (via raw string
# extraction, since mdb-tools wasn't available in the build sandbox), we
# confirmed these tables exist: a well-master table, "Data-Rainfall",
# "Master - Rainfall Station", "Master - DWLR", plus lithology/log tables
# ("Log General", "Log Detail") and a water-level readings table (columns
# include WellNo, PW-SWL, OW1-SWL, OW2-SWL, OW3-SWL, Date). We could not
# confirm the *exact* table name strings for the well-master and
# water-level tables from string extraction alone (Access stores those in
# a binary catalog page we couldn't decode without mdb-tools). Run the
# `mdb-tables` line below FIRST and adjust load_to_postgres.py's
# TABLE_NAME_MAP to match what you actually see.

set -euo pipefail
MDB_PATH="${1:?Usage: export_mdb.sh <path-to-mdb> <output-dir>}"
OUT_DIR="${2:?Usage: export_mdb.sh <path-to-mdb> <output-dir>}"
mkdir -p "$OUT_DIR"

echo "== Tables found in $MDB_PATH =="
mdb-tables -1 "$MDB_PATH" | tee "$OUT_DIR/_table_list.txt"

echo "== Exporting each table to CSV =="
while read -r TBL; do
    # Skip Access system tables
    case "$TBL" in MSys*) continue;; esac
    SAFE_NAME=$(echo "$TBL" | tr ' /' '__')
    echo "  -> $TBL  =>  $OUT_DIR/${SAFE_NAME}.csv"
    mdb-export "$MDB_PATH" "$TBL" > "$OUT_DIR/${SAFE_NAME}.csv"
done < "$OUT_DIR/_table_list.txt"

echo "Done. Inspect $OUT_DIR/_table_list.txt and the CSVs, then update"
echo "etl/load_to_postgres.py's TABLE_NAME_MAP to point at the real files."
