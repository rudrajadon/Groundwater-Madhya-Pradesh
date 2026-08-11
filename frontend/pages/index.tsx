import dynamic from "next/dynamic";
import { useState } from "react";
import { getForecast, getForecastByWellId, getWellHistory, ForecastResponse } from "../lib/api";
import ForecastChart from "../components/ForecastChart";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

// Leaflet touches `window` — must be loaded client-side only, standard
// pattern for react-leaflet inside Next.js.
const GroundwaterMap = dynamic(() => import("../components/Map"), { ssr: false });

export default function Home() {
  const [pointForecast, setPointForecast] = useState<ForecastResponse | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleWellSelect(wellId: string) {
    setLoading(true);
    setError(null);
    try {
      const [h, fc] = await Promise.all([
        getWellHistory(wellId).catch(e => { console.warn(e); return { readings: [] }; }),
        getForecastByWellId(wellId)
      ]);
      setHistory(h.readings || []);
      setPointForecast(fc);
    } catch (e: any) {
      setError(e.message);
      setPointForecast(null);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }

  const historyChartData = history.map((r: any) => ({
    date: r.date,
    head: r.head_msl_m,
    depth: r.depth_bgl_m,
  }));

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <div style={{ flex: 2 }}>
        <GroundwaterMap onWellSelect={handleWellSelect} />
      </div>
      
      <aside style={{ flex: 1, padding: 24, overflowY: "auto", borderLeft: "1px solid #e5e7eb", background: "#f9fafb" }}>
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600, color: "#111827" }}>Madhya Pradesh</h2>
          <h3 style={{ margin: "4px 0 0 0", fontSize: 16, fontWeight: 400, color: "#6b7280" }}>Groundwater Forecast</h3>
          <p style={{ color: "#9ca3af", fontSize: 13, margin: "12px 0 0 0" }}>
            Click a well marker to view detailed forecast
          </p>
        </div>
        
        {loading && (
          <div style={{ padding: 20, textAlign: "center", color: "#6b7280" }}>
            Loading...
          </div>
        )}
        
        {error && (
          <div style={{ padding: 16, background: "#fee2e2", color: "#991b1b", borderRadius: 8, fontSize: 14 }}>
            {error}
          </div>
        )}
        
        {pointForecast && !loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* Well Info Card */}
            <div style={{ background: "#fff", padding: 20, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: "#111827" }}>
                {pointForecast.well_id.startsWith('POINT_') ? (
                  (() => {
                    const parts = pointForecast.well_id.replace('POINT_', '').split('_');
                    const lat = parseFloat(parts[0]);
                    const lon = parseFloat(parts[1]);
                    const latDir = lat >= 0 ? 'N' : 'S';
                    const lonDir = lon >= 0 ? 'E' : 'W';
                    return `Location: ${Math.abs(lat).toFixed(2)}°${latDir}, ${Math.abs(lon).toFixed(2)}°${lonDir}`;
                  })()
                ) : (
                  pointForecast.well_id
                )}
              </h3>
              {pointForecast.aquifer_zone && (
                <p style={{ margin: "4px 0 0 0", fontSize: 14, color: "#6b7280" }}>
                  {pointForecast.aquifer_zone}
                </p>
              )}
            </div>

            {/* Trend Status Card */}
            <div style={{ 
              background: pointForecast.trend_label === "Critical" ? "#fef2f2"
                : pointForecast.trend_label === "Watch" ? "#fffbeb"
                : pointForecast.trend_label === "Stable" ? "#f0fdf4" : "#f9fafb",
              padding: 20, 
              borderRadius: 12,
              border: `2px solid ${
                pointForecast.trend_label === "Critical" ? "#fecaca"
                : pointForecast.trend_label === "Watch" ? "#fde68a"
                : pointForecast.trend_label === "Stable" ? "#bbf7d0" : "#e5e7eb"
              }`
            }}>
              <div style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", color: "#6b7280", marginBottom: 4 }}>
                Status
              </div>
              <div style={{ 
                fontSize: 24, 
                fontWeight: 700,
                color: pointForecast.trend_label === "Critical" ? "#dc2626"
                  : pointForecast.trend_label === "Watch" ? "#d97706"
                  : pointForecast.trend_label === "Stable" ? "#16a34a" : "#6b7280"
              }}>
                {pointForecast.trend_label}
              </div>
              <p style={{ margin: "12px 0 0 0", fontSize: 14, color: "#374151", lineHeight: "1.5" }}>
                {pointForecast.recommendation}
              </p>
            </div>

            {/* Historical Chart */}
            {history.length > 0 && (
              <div style={{ background: "#fff", padding: 20, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
                <h4 style={{ margin: "0 0 16px 0", fontSize: 14, fontWeight: 600, color: "#111827" }}>
                  Historical Water Levels
                </h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={historyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#6b7280" }} />
                    <YAxis tick={{ fontSize: 11, fill: "#6b7280" }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="head" stroke="#2563eb" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            
            {/* 12-Month Forecast Chart */}
            <div style={{ background: "#fff", padding: 20, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
              <h4 style={{ margin: "0 0 16px 0", fontSize: 14, fontWeight: 600, color: "#111827" }}>
                12-Month Forecast
              </h4>
              <ForecastChart data={pointForecast.forecast} />
            </div>

            {/* Data Quality Indicator (only show for low confidence) */}
            {(pointForecast.model_version === "statistical_v1" || pointForecast.model_version === "statistical_limited_data" || !pointForecast.matched_existing_well) && (
              <div style={{ 
                padding: 12, 
                background: "#f3f4f6", 
                borderRadius: 8,
                fontSize: 12,
                color: "#6b7280",
                borderLeft: "3px solid #9ca3af"
              }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>Data Quality</div>
                {!pointForecast.matched_existing_well && pointForecast.distance_to_nearest_well_km ? (
                  <div>Estimated forecast: {pointForecast.distance_to_nearest_well_km.toFixed(1)}km from nearest monitoring well</div>
                ) : pointForecast.model_version?.includes("statistical") ? (
                  <div>Forecast based on statistical trend analysis</div>
                ) : null}
              </div>
            )}
          </div>
        )}

        {!pointForecast && !loading && !error && null}
      </aside>
    </div>
  );
}
