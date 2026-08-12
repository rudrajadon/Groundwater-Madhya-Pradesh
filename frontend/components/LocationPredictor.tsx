import { useState } from "react";
import { ForecastResponse, ForecastPoint } from "../lib/api";
import { getNearestWells, NearestWellsResponse } from "../lib/location-api";
import ForecastChart from "./ForecastChart";

interface LocationPredictorProps {
  onClose: () => void;
  initialLat?: number;
  initialLon?: number;
}

export default function LocationPredictor({ onClose, initialLat, initialLon }: LocationPredictorProps) {
  const [lat, setLat] = useState(initialLat?.toString() || "");
  const [lon, setLon] = useState(initialLon?.toString() || "");
  const [kNeighbors, setKNeighbors] = useState(5);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [nearestWells, setNearestWells] = useState<NearestWellsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showWellsInfo, setShowWellsInfo] = useState(false);

  const handleGPS = () => {
    if (!navigator.geolocation) {
      setError("GPS not supported by your browser");
      return;
    }

    setGpsLoading(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        setLat(latitude.toFixed(4));
        setLon(longitude.toFixed(4));
        setGpsLoading(false);
      },
      (err) => {
        setGpsLoading(false);
        setError(`GPS error: ${err.message}. Check location permissions.`);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  };

  const handlePredict = async () => {
    const latitude = parseFloat(lat);
    const longitude = parseFloat(lon);

    // Validate inputs
    if (isNaN(latitude) || isNaN(longitude)) {
      setError("Please enter valid latitude and longitude");
      return;
    }

    if (latitude < 21.0 || latitude > 26.9) {
      setError("Latitude must be within Madhya Pradesh bounds (21.0°N - 26.9°N)");
      return;
    }

    if (longitude < 74.0 || longitude > 82.8) {
      setError("Longitude must be within Madhya Pradesh bounds (74.0°E - 82.8°E)");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Import predictCustomLocation dynamically to avoid import issues
      const { predictCustomLocation } = await import("../lib/location-api");
      
      // Get forecast and nearest wells info in parallel
      const [forecastData, wellsData] = await Promise.all([
        predictCustomLocation(latitude, longitude, kNeighbors),
        getNearestWells(latitude, longitude, kNeighbors),
      ]);

      setForecast(forecastData);
      setNearestWells(wellsData);
    } catch (err: any) {
      setError(err.message || "Failed to generate forecast");
      setForecast(null);
      setNearestWells(null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handlePredict();
    }
  };

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(0, 0, 0, 0.5)",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      zIndex: 2000,
    }}>
      <div style={{
        background: "#fff",
        borderRadius: "16px",
        boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
        maxWidth: "600px",
        width: "90%",
        maxHeight: "90vh",
        overflow: "auto",
        padding: "24px",
      }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 600, color: "#111827" }}>
              Custom Location Predictor
            </h2>
            <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "#6b7280" }}>
              Get groundwater forecast for any location in Madhya Pradesh
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              fontSize: "24px",
              cursor: "pointer",
              color: "#6b7280",
              padding: "4px 8px",
            }}
          >
            ×
          </button>
        </div>

        {/* Input Form */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* GPS Button */}
          <button
            onClick={handleGPS}
            disabled={gpsLoading}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              padding: "12px",
              background: gpsLoading ? "#e5e7eb" : "#3b82f6",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              fontSize: "14px",
              fontWeight: 600,
              cursor: gpsLoading ? "not-allowed" : "pointer",
            }}
          >
            {gpsLoading ? "Getting your location..." : "Use My Current Location (GPS)"}
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{ flex: 1, height: "1px", background: "#e5e7eb" }}></div>
            <span style={{ fontSize: "12px", color: "#9ca3af" }}>OR</span>
            <div style={{ flex: 1, height: "1px", background: "#e5e7eb" }}></div>
          </div>

          {/* Manual Input */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#111827", marginBottom: "8px" }}>
                Latitude (°N)
              </label>
              <input
                type="number"
                step="0.0001"
                min="21.0"
                max="26.9"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="e.g. 23.5"
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "1px solid #d1d5db",
                  borderRadius: "8px",
                  fontSize: "14px",
                  boxSizing: "border-box",
                }}
              />
              <span style={{ fontSize: "11px", color: "#9ca3af" }}>21.0 - 26.9</span>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#111827", marginBottom: "8px" }}>
                Longitude (°E)
              </label>
              <input
                type="number"
                step="0.0001"
                min="74.0"
                max="82.8"
                value={lon}
                onChange={(e) => setLon(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="e.g. 77.4"
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "1px solid #d1d5db",
                  borderRadius: "8px",
                  fontSize: "14px",
                  boxSizing: "border-box",
                }}
              />
              <span style={{ fontSize: "11px", color: "#9ca3af" }}>74.0 - 82.8</span>
            </div>
          </div>

          {/* K Neighbors Slider */}
          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#111827", marginBottom: "8px" }}>
              Nearest Wells: {kNeighbors}
            </label>
            <input
              type="range"
              min="3"
              max="10"
              value={kNeighbors}
              onChange={(e) => setKNeighbors(parseInt(e.target.value))}
              style={{ width: "100%" }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#9ca3af" }}>
              <span>3 (less smooth)</span>
              <span>10 (more smooth)</span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              padding: "12px",
              background: "#fee2e2",
              color: "#991b1b",
              borderRadius: "8px",
              fontSize: "13px",
            }}>
              {error}
            </div>
          )}

          {/* Predict Button */}
          <button
            onClick={handlePredict}
            disabled={loading || !lat || !lon}
            style={{
              padding: "12px",
              background: loading || !lat || !lon ? "#e5e7eb" : "#10b981",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              fontSize: "14px",
              fontWeight: 600,
              cursor: loading || !lat || !lon ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Generating Forecast..." : "Generate Forecast"}
          </button>
        </div>

        {/* Results */}
        {forecast && nearestWells && (
          <div style={{ marginTop: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* Location Info */}
            <div style={{
              background: "#f0fdf4",
              padding: "16px",
              borderRadius: "8px",
              border: "2px solid #bbf7d0",
            }}>
              <div style={{ fontSize: "12px", fontWeight: 600, textTransform: "uppercase", color: "#6b7280", marginBottom: "4px" }}>
                Custom Location
              </div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "#16a34a", marginBottom: "8px" }}>
                {parseFloat(lat).toFixed(4)}°N, {parseFloat(lon).toFixed(4)}°E
              </div>
              <div style={{ fontSize: "13px", color: "#374151" }}>
                {forecast.aquifer_zone} • Interpolated from {nearestWells.count} wells
              </div>
            </div>

            {/* Trend Status */}
            <div style={{
              background: forecast.trend_label === "Critical" ? "#fef2f2"
                : forecast.trend_label === "Watch" ? "#fffbeb"
                : forecast.trend_label === "Stable" ? "#f0fdf4" : "#f9fafb",
              padding: "16px",
              borderRadius: "8px",
              border: `2px solid ${
                forecast.trend_label === "Critical" ? "#fecaca"
                : forecast.trend_label === "Watch" ? "#fde68a"
                : forecast.trend_label === "Stable" ? "#bbf7d0" : "#e5e7eb"
              }`,
            }}>
              <div style={{ fontSize: "12px", fontWeight: 600, textTransform: "uppercase", color: "#6b7280", marginBottom: "4px" }}>
                Forecast Trend
              </div>
              <div style={{
                fontSize: "24px",
                fontWeight: 700,
                color: forecast.trend_label === "Critical" ? "#dc2626"
                  : forecast.trend_label === "Watch" ? "#d97706"
                  : forecast.trend_label === "Stable" ? "#16a34a" : "#6b7280",
                marginBottom: "8px",
              }}>
                {forecast.trend_label}
              </div>
              <p style={{ margin: 0, fontSize: "13px", color: "#374151", lineHeight: "1.5" }}>
                {forecast.recommendation}
              </p>
            </div>

            {/* Nearest Wells Info */}
            <div>
              <button
                onClick={() => setShowWellsInfo(!showWellsInfo)}
                style={{
                  width: "100%",
                  padding: "12px",
                  background: "#f3f4f6",
                  border: "1px solid #d1d5db",
                  borderRadius: "8px",
                  fontSize: "13px",
                  fontWeight: 600,
                  color: "#374151",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>Nearest Wells Info ({nearestWells.count})</span>
                <span>{showWellsInfo ? "▼" : "▶"}</span>
              </button>

              {showWellsInfo && (
                <div style={{ marginTop: "8px", fontSize: "12px" }}>
                  <div style={{ marginBottom: "8px", color: "#6b7280" }}>
                    Avg Distance: {nearestWells.avg_distance_km} km • Max: {nearestWells.max_distance_km} km
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {nearestWells.nearest_wells.map((well, idx) => (
                      <div
                        key={well.well_id}
                        style={{
                          background: "#fff",
                          padding: "8px",
                          borderRadius: "4px",
                          border: "1px solid #e5e7eb",
                        }}
                      >
                        <div style={{ fontWeight: 600, color: "#111827" }}>
                          {idx + 1}. {well.well_id}
                        </div>
                        <div style={{ color: "#6b7280", marginTop: "2px" }}>
                          {well.distance_km.toFixed(2)} km away • Weight: {(well.interpolation_weight * 100).toFixed(1)}%
                        </div>
                        <div style={{ color: "#9ca3af", fontSize: "11px", marginTop: "2px" }}>
                          {well.geology_type} • {well.block}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Forecast Chart */}
            <div style={{
              background: "#fff",
              padding: "16px",
              borderRadius: "8px",
              border: "1px solid #e5e7eb",
            }}>
              <h4 style={{ margin: "0 0 12px 0", fontSize: "14px", fontWeight: 600, color: "#111827" }}>
                12-Month Forecast with Uncertainty
              </h4>
              <ForecastChart data={forecast.forecast} />
            </div>

            {/* Caveat */}
            <div style={{
              padding: "12px",
              background: "#fffbeb",
              borderRadius: "8px",
              fontSize: "12px",
              color: "#92400e",
              borderLeft: "3px solid #fbbf24",
            }}>
              <div style={{ fontWeight: 600, marginBottom: "4px" }}>⚠️ Interpolation Notice</div>
              {forecast.caveat}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
