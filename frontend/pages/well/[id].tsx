import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { getForecastByWellId, getWellHistory, getWells, ForecastResponse, WellSummary } from "../../lib/api";
import ForecastChart from "../../components/ForecastChart";
import RainfallChart from "../../components/RainfallChart";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

export default function WellDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [history, setHistory] = useState<any[]>([]);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [rainfall, setRainfall] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Check dark mode from localStorage
    const isDark = localStorage.getItem('darkMode') === 'true';
    setDarkMode(isDark);
    
    if (typeof id !== "string") return;
    setLoading(true);

    // Fetch history
    getWellHistory(id)
      .then((h) => setHistory(h.readings))
      .catch((e) => setError(e.message));

    // Fetch forecast directly by well ID
    getForecastByWellId(id)
      .then((fc) => setForecast(fc))
      .catch((e) => {
        // Forecast may fail if model isn't loaded — not a fatal error
        console.warn("Could not load forecast:", e.message);
      })
      .finally(() => setLoading(false));
    
    // Fetch rainfall data
    fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/v1/wells/${id}/rainfall`)
      .then(res => res.json())
      .then(data => {
        if (data.rainfall_data) {
          setRainfall(data.rainfall_data);
        }
      })
      .catch(e => console.warn("Could not load rainfall:", e.message));
  }, [id]);

  const historyChartData = history.map((r: any) => ({
    date: r.date,
    head: r.head_msl_m,
    depth: r.depth_bgl_m,
  }));

  return (
    <div className="well-detail-container">
      <div className="well-header">
        <button 
          onClick={() => router.push("/")} 
          className="back-button"
          style={{
            color: darkMode ? "#cbd5e1" : "#475569",
            borderColor: darkMode ? "#475569" : "#cbd5e1",
          }}
        >
          &larr; Back to map
        </button>
        <h1 style={{ color: "var(--accent-primary)", fontSize: "2.5rem", marginBottom: 8 }}>Well {id}</h1>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>Historical data and 12-month predictions.</p>
      </div>

      {error && (
        <div style={{ padding: 16, background: "rgba(239, 68, 68, 0.1)", border: "1px solid var(--danger)", borderRadius: 8, color: "var(--text-primary)" }}>
          <p style={{ margin: 0 }}>{error}</p>
        </div>
      )}

      <div className="glass-panel" style={{ padding: 32 }}>
        <h3 style={{ borderBottom: "1px solid var(--border-color)", paddingBottom: 16, marginTop: 0 }}>Historical Water Levels</h3>
        {history.length === 0 ? (
          <p style={{ color: "var(--text-secondary)" }}>{loading ? "Loading history…" : "No readings found."}</p>
        ) : (
          <div style={{ marginTop: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h3 style={{ margin: 0, borderBottom: "none" }}>Historical Readings</h3>
              <span style={{ fontSize: 13, color: "var(--text-secondary)", fontWeight: 500, padding: "4px 12px", background: "var(--bg-secondary)", borderRadius: "6px" }}>
                {(() => {
                  const dates = history.map((r: any) => new Date(r.date));
                  const oldestDate = new Date(Math.min(...dates.map(d => d.getTime())));
                  const newestDate = new Date(Math.max(...dates.map(d => d.getTime())));
                  const yearsDiff = (newestDate.getTime() - oldestDate.getTime()) / (1000 * 60 * 60 * 24 * 365.25);
                  const years = Math.floor(yearsDiff);
                  
                  return years >= 1 
                    ? `${years} year${years > 1 ? 's' : ''} of data (${history.length} readings)`
                    : `${history.length} readings`;
                })()}
              </span>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
              <LineChart data={historyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="var(--text-secondary)" />
                <YAxis 
                  label={{ value: "Head (m MSL)", angle: -90, position: "insideLeft", fill: "var(--text-secondary)" }} 
                  stroke="var(--text-secondary)"
                  domain={['auto', 'auto']}
                  tickFormatter={(value) => value.toFixed(1)}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: "var(--bg-tertiary)", borderColor: "var(--border-color)", color: "var(--text-primary)" }}
                  formatter={(value: number) => value.toFixed(2) + " m MSL"}
                />
                <Line type="monotone" dataKey="head" name="Hydraulic Head" stroke="var(--accent-secondary)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Rainfall Chart */}
      {rainfall.length > 0 && (
        <div className="glass-panel" style={{ padding: 32 }}>
          <RainfallChart data={rainfall} darkMode={darkMode} />
        </div>
      )}

      <div className="glass-panel" style={{ padding: 32 }}>
        <h3 style={{ borderBottom: "1px solid var(--border-color)", paddingBottom: 16, marginTop: 0 }}>12-Month Forecast</h3>
        {loading && <p style={{ color: "var(--accent-primary)" }}>Running inference model…</p>}
        {forecast ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 16 }}>
            <div className="forecast-info" style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <strong style={{ fontSize: 18 }}>Trend:</strong>{" "}
              <span style={{
                padding: "6px 12px", 
                borderRadius: 6, 
                fontSize: 16,
                fontWeight: 600,
                background: forecast.trend_label === "Critical" ? "rgba(239, 68, 68, 0.2)" : 
                            forecast.trend_label === "Watch" ? "rgba(245, 158, 11, 0.2)" : "rgba(16, 185, 129, 0.2)",
                color: forecast.trend_label === "Critical" ? "var(--danger)" : 
                       forecast.trend_label === "Watch" ? "var(--warning)" : "var(--success)"
              }}>
                {forecast.trend_label}
              </span>
            </div>
            <p style={{ fontSize: 16, color: "var(--text-primary)", background: "rgba(255, 255, 255, 0.05)", padding: 16, borderRadius: 8, lineHeight: 1.5 }}>{forecast.recommendation}</p>
            {forecast.caveat && (
              <div style={{ fontSize: 14, color: "var(--warning)", background: "rgba(245, 158, 11, 0.1)", border: "1px solid rgba(245, 158, 11, 0.2)", padding: 16, borderRadius: 8, lineHeight: 1.5 }}>
                {forecast.caveat}
              </div>
            )}
            <div style={{ marginTop: 16 }} className="chart-container">
              <ForecastChart data={forecast.forecast} />
            </div>
          </div>
        ) : (
          !loading && <p style={{ color: "var(--text-secondary)" }}>Forecast not available (model may not be loaded).</p>
        )}
      </div>
    </div>
  );
}
