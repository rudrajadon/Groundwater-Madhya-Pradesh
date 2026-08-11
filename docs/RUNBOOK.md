# Runbook — getting this running in YOUR environment

This repo was written in a sandbox with **no network access**, no Docker,
no Postgres, and no `torch`/`fastapi`/`node_modules` installed — so none of
it could be executed end-to-end here. Every file was syntax-checked
(`py_compile`/`ast.parse` for Python, JSON validation for configs) but not
run. Follow this runbook in your own environment, in order.

## 1. Data (etl/)
```bash
# On a machine with mdb-tools installed (apt-get install mdbtools / brew install mdbtools):
./etl/export_mdb.sh /path/to/IndorePZ.mdb ./raw_csv
cat ./raw_csv/_table_list.txt        # <- confirm real table names here
# Edit etl/load_to_postgres.py's TABLE_NAME_MAP + WELL_COLUMN_MAP to match
# what you actually see (placeholders are marked PLACEHOLDER_*).

docker compose -f infra/docker-compose.yml up -d db
psql postgresql://gwuser:changeme@localhost:5432/groundwater -f etl/schema.sql
export DATABASE_URL=postgresql://gwuser:changeme@localhost:5432/groundwater
pip install -r etl/requirements.txt   # (create this: pandas, psycopg2-binary, requests)
python etl/load_to_postgres.py --csv-dir ./raw_csv
python etl/fetch_rainfall_openmeteo.py --days-back 90
```

## 2. Model (ml/)
```bash
pip install -r ml/requirements.txt
# Export wells.csv / litho.csv / water_levels.csv from Postgres, matching
# the column names preprocessing.py expects (see that file's docstrings),
# OR point train.py at your already-working Book2.xlsx-derived CSVs.
python ml/train.py --data-dir ./data --save-dir ./ml/artifacts
# Confirm ml/artifacts/model_metadata.json shows RMSE/R2 close to the
# notebook's own v3 numbers (RMSE~3.40, R2~0.65) as a sanity check that
# the extraction into preprocessing.py/model.py didn't introduce drift.
```

## 3. Backend
```bash
pip install -r backend/requirements.txt
# Finish the TODO in backend/app/main.py: load ForecastModel at startup
# and wire it into backend/app/routers/forecast.py (currently a clearly
# labeled 501 stub — the endpoint contract is final, only this wiring
# step remains).
cd backend && uvicorn app.main:app --reload
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/wells
```

## 4. Frontend
```bash
cd frontend
npm install
npm run dev
# open http://localhost:3000
```

## 5. Everything together
```bash
docker compose -f infra/docker-compose.yml up --build
```

## What's genuinely done vs. what's a labeled stub
- **Done, extracted faithfully from the notebook:** ml/preprocessing.py,
  ml/model.py, ml/train.py — these are the real PGNN-LSTM v3 logic.
- **Done, new code:** etl coordinate parser (tested against real sample
  DMS strings from the mdb), backend routers, dynamic graph-extension
  service, recommendation heuristic, full frontend.
- **Explicitly stubbed, not faked:** the forecast endpoint's model call
  (needs a trained artifact from step 2), and the exact mdb table/column
  names in load_to_postgres.py (needs mdb-tools output, which this sandbox
  couldn't produce — confirmed no network access when attempting to
  install it).
