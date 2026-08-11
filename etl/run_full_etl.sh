#!/usr/bin/env bash
#
# Full ETL pipeline to process ALL MDB files from GW_Data
#
# Prerequisites:
#   1. mdb-tools installed: brew install mdbtools
#   2. PostgreSQL running with PostGIS extension
#   3. Python venv with requirements installed
#
# Usage:
#   export DATABASE_URL=postgresql://user:pass@localhost:5432/groundwater
#   ./run_full_etl.sh

set -euo pipefail

# Configuration
DATA_DIR="../GW_Data"
CSV_OUTPUT="./raw_csv_all"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "Groundwater ETL - Process ALL MDB Files"
echo "========================================"
echo ""

# Check DATABASE_URL
if [ -z "${DATABASE_URL:-}" ]; then
    echo "ERROR: DATABASE_URL not set"
    echo "Example: export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/groundwater"
    exit 1
fi

echo "✓ DATABASE_URL: ${DATABASE_URL}"

# Check mdb-tools
if ! command -v mdb-tables &> /dev/null; then
    echo "ERROR: mdb-tools not found"
    echo "Install with: brew install mdbtools"
    exit 1
fi

echo "✓ mdb-tools installed"

# Check Python venv
if [ ! -d "../etl_venv" ] && [ ! -d ".venv" ]; then
    echo "ERROR: No Python virtual environment found"
    echo "Create with: python3 -m venv ../etl_venv && source ../etl_venv/bin/activate"
    echo "Then install: pip install -r requirements.txt"
    exit 1
fi

# Activate venv
if [ -d "../etl_venv" ]; then
    source ../etl_venv/bin/activate
    echo "✓ Activated ../etl_venv"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ Activated .venv"
fi

# Check Python dependencies
python -c "import pandas, psycopg2" 2>/dev/null || {
    echo "ERROR: Required Python packages not installed"
    echo "Install with: pip install -r requirements.txt"
    exit 1
}

echo "✓ Python dependencies OK"
echo ""

# Apply schema updates
echo "Applying schema updates..."
psql "${DATABASE_URL}" -c "ALTER TABLE wells ADD COLUMN IF NOT EXISTS source_file TEXT;" || true
echo "✓ Schema updated"
echo ""

# Process all MDB files
echo "Processing all MDB files from ${DATA_DIR}..."
echo ""
cd "${SCRIPT_DIR}"
python process_all_mdb.py --data-dir "${DATA_DIR}" --csv-output "${CSV_OUTPUT}"

echo ""
echo "========================================"
echo "ETL Complete!"
echo "========================================"
echo ""
echo "Summary statistics:"
psql "${DATABASE_URL}" -c "
    SELECT 
        COUNT(DISTINCT well_id) as total_wells,
        COUNT(DISTINCT district) as districts,
        COUNT(DISTINCT source_file) as source_files
    FROM wells;
"
echo ""
psql "${DATABASE_URL}" -c "
    SELECT 
        COUNT(*) as total_readings,
        MIN(date) as earliest_date,
        MAX(date) as latest_date
    FROM readings;
"
echo ""
echo "Wells by district:"
psql "${DATABASE_URL}" -c "
    SELECT 
        district,
        COUNT(*) as well_count,
        SUM(CASE WHEN coord_validated THEN 1 ELSE 0 END) as validated_coords
    FROM wells
    GROUP BY district
    ORDER BY well_count DESC;
"

echo ""
echo "✓ All done! Check the output above for data quality issues."
echo ""
