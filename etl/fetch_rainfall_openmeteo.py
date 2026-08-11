"""
Pull recent daily rainfall for each rainfall station (or well location, if
no dedicated stations) from the Open-Meteo Historical Weather API — free,
no API key, no signup (see https://open-meteo.com/en/docs/historical-weather-api).

This keeps the model's 24-month input window current between refreshes of
the source .mdb file. It does NOT fetch weather forecasts — the model does
not need future rainfall (see project plan, Section 4.4); it only needs
recent *actual* rainfall backfilled.

Usage:
  export DATABASE_URL=postgresql://user:pass@localhost/groundwater
  python fetch_rainfall_openmeteo.py --days-back 90
"""
import argparse
import os
import sys
from datetime import date, timedelta

import psycopg2
import requests

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_station_rainfall(lat: float, lon: float, start: date, end: date) -> list[tuple[date, float]]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "precipitation_sum",
        "timezone": "Asia/Kolkata",
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    dates = data.get("daily", {}).get("time", [])
    vals = data.get("daily", {}).get("precipitation_sum", [])
    return list(zip([date.fromisoformat(d) for d in dates], vals))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days-back", type=int, default=90)
    args = ap.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        sys.exit("Set DATABASE_URL env var")

    conn = psycopg2.connect(db_url)
    end = date.today()
    start = end - timedelta(days=args.days_back)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT station_name, ST_Y(geom::geometry), ST_X(geom::geometry)
            FROM rainfall_stations WHERE geom IS NOT NULL
        """)
        stations = cur.fetchall()

    if not stations:
        print("No rainfall stations with coordinates found — nothing to fetch.")
        return

    for name, lat, lon in stations:
        try:
            readings = fetch_station_rainfall(lat, lon, start, end)
        except Exception as e:
            print(f"[warn] {name}: fetch failed ({e})", file=sys.stderr)
            continue
        with conn.cursor() as cur:
            for d, mm in readings:
                if mm is None:
                    continue
                cur.execute("""
                    INSERT INTO rainfall_readings (station_name, date, rainfall_mm, source)
                    VALUES (%s, %s, %s, 'open_meteo')
                    ON CONFLICT (station_name, date) DO NOTHING
                """, (name, d, mm))
        conn.commit()
        print(f"{name}: {len(readings)} days loaded")

    conn.close()


if __name__ == "__main__":
    main()
