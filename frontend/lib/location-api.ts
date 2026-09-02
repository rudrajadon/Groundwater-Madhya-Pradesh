// Custom Location Predictor API Client
import { ForecastResponse } from "./api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export interface NearestWell {
  well_id: string;
  distance_km: number;
  interpolation_weight: number;
  geology_type: string;
  aquifer_classification: string;
  trend_label: string;
  block: string;
  district: string;
  lat: number;
  lon: number;
}

export interface NearestWellsResponse {
  count: number;
  nearest_wells: NearestWell[];
  avg_distance_km: number;
  max_distance_km: number;
}

/**
 * Get groundwater forecast for a custom location using spatial interpolation
 */
export async function predictCustomLocation(
  latitude: number,
  longitude: number,
  kNeighbors: number = 5
): Promise<ForecastResponse> {
  const url = `${API_BASE}/api/v1/location/predict?lat=${latitude}&lon=${longitude}&k_neighbors=${kNeighbors}`;
  
  const response = await fetch(url, { method: "POST" });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to get forecast: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get nearest wells info for a location
 */
export async function getNearestWells(
  latitude: number,
  longitude: number,
  k: number = 5
): Promise<NearestWellsResponse> {
  const url = `${API_BASE}/api/v1/location/nearest-wells?lat=${latitude}&lon=${longitude}&k=${k}`;
  
  const response = await fetch(url);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to get nearest wells: ${response.statusText}`);
  }
  
  const data = await response.json();
  
  // Transform to match our interface
  return {
    count: data.count,
    nearest_wells: data.nearest_wells,
    avg_distance_km: parseFloat(data.avg_distance_km),
    max_distance_km: parseFloat(data.max_distance_km),
  };
}
