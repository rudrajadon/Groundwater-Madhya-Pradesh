const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export interface WellSummary {
  well_id: string;
  lat: number;
  lon: number;
  block?: string;
  aquifer_zone?: string;
  trend_label?: "Stable" | "Watch" | "Critical" | null;
  geology_type?: "Basalt" | "Granite" | "Vindhyan" | "Unknown" | null;
  aquifer_classification?: "Weathered" | "Fractured" | "Massive" | null;
}

export interface ForecastPoint {
  month_index: number;
  head_msl_m: number;
  lower_m: number;
  upper_m: number;
}

export interface ForecastResponse {
  well_id: string;
  matched_existing_well: boolean;
  distance_to_nearest_well_km?: number;
  aquifer_zone: string;
  forecast: ForecastPoint[];
  trend_label: string;
  recommendation: string;
  model_version: string;
  caveat?: string;
}

export async function getWells(): Promise<WellSummary[]> {
  const res = await fetch(`${API_BASE}/api/v1/wells`);
  if (!res.ok) throw new Error(`Failed to fetch wells: ${res.status}`);
  return res.json();
}

export async function getWellHistory(wellId: string) {
  const res = await fetch(`${API_BASE}/api/v1/wells/${encodeURIComponent(wellId)}/history`);
  if (!res.ok) throw new Error(`Failed to fetch history: ${res.status}`);
  return res.json();
}

export async function getForecast(lat: number, lon: number): Promise<ForecastResponse> {
  const res = await fetch(`${API_BASE}/api/v1/forecast?lat=${lat}&lon=${lon}`);
  if (!res.ok) throw new Error(`Failed to fetch forecast: ${res.status}`);
  return res.json();
}

export async function getForecastByWellId(wellId: string): Promise<ForecastResponse> {
  const res = await fetch(`${API_BASE}/api/v1/forecast/well/${encodeURIComponent(wellId)}`);
  if (!res.ok) throw new Error(`Failed to fetch well forecast: ${res.status}`);
  return res.json();
}
