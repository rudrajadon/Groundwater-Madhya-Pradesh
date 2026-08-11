#!/usr/bin/env python3
"""
Fetch elevation data for wells missing elevation_m.
Uses Open-Elevation API (free, no API key required).
"""
import psycopg2
import requests
import time
from typing import List, Tuple

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "groundwater",
    "user": "gwuser",
    "password": "changeme"
}

def get_wells_missing_elevation(conn) -> List[Tuple[str, float, float]]:
    """Get wells that have readings but no elevation (focusing on Unknown trend wells)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                w.well_id,
                ST_Y(w.geom::geometry) as lat,
                ST_X(w.geom::geometry) as lon
            FROM wells w
            INNER JOIN readings r ON w.well_id = r.well_id
            WHERE w.elevation_m IS NULL
              AND w.geom IS NOT NULL
              AND r.depth_bgl_m IS NOT NULL
              AND r.head_msl_m IS NULL
              AND w.trend_label = 'Unknown'
            ORDER BY w.well_id;
        """)
        return cur.fetchall()

def fetch_elevation_batch(coords: List[Tuple[float, float]]) -> List[float]:
    """
    Fetch elevations using Open-Elevation API.
    Handles batches of up to 100 coordinates.
    """
    if not coords:
        return []
    
    # Open-Elevation expects {"locations": [{"latitude": lat, "longitude": lon}, ...]}
    locations = [{"latitude": lat, "longitude": lon} for lat, lon in coords]
    
    try:
        response = requests.post(
            "https://api.open-elevation.com/api/v1/lookup",
            json={"locations": locations},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return [result["elevation"] for result in data["results"]]
    except Exception as e:
        print(f"Error fetching elevations: {e}")
        # Fallback: use rough average elevation for MP (~500m)
        return [500.0] * len(coords)

def update_well_elevation(conn, well_id: str, elevation: float):
    """Update elevation for a single well."""
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE wells 
            SET elevation_m = %s
            WHERE well_id = %s;
        """, (elevation, well_id))

def compute_head_from_depth(conn, well_id: str, elevation: float):
    """Compute head_msl_m = elevation_m - depth_bgl_m for all readings."""
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE readings
            SET head_msl_m = %s - depth_bgl_m
            WHERE well_id = %s
              AND depth_bgl_m IS NOT NULL
              AND head_msl_m IS NULL;
        """, (elevation, well_id))
        return cur.rowcount

def main():
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    
    try:
        # Get wells missing elevation
        wells = get_wells_missing_elevation(conn)
        print(f"Found {len(wells)} wells missing elevation data\n")
        
        if not wells:
            print("No wells to update!")
            return
        
        # Process in batches of 20 (to avoid API rate limits)
        batch_size = 20
        total_updated = 0
        total_readings = 0
        
        for i in range(0, len(wells), batch_size):
            batch = wells[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(wells)-1)//batch_size + 1}...")
            
            # Extract coordinates
            well_ids = [w[0] for w in batch]
            coords = [(w[1], w[2]) for w in batch]
            
            # Fetch elevations
            elevations = fetch_elevation_batch(coords)
            
            # Update database
            for well_id, (lat, lon), elevation in zip(well_ids, coords, elevations):
                # Update well elevation
                update_well_elevation(conn, well_id, elevation)
                
                # Compute head_msl_m for all readings
                readings_updated = compute_head_from_depth(conn, well_id, elevation)
                
                print(f"  {well_id}: elevation={elevation:.1f}m, updated {readings_updated} readings")
                total_updated += 1
                total_readings += readings_updated
            
            conn.commit()
            
            # Be nice to the API
            if i + batch_size < len(wells):
                time.sleep(2)
        
        print(f"\n✓ Updated {total_updated} wells with elevation data")
        print(f"✓ Computed head_msl_m for {total_readings} readings")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
