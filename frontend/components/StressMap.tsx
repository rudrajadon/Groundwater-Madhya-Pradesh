import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

interface DistrictStress {
  district: string;
  total_wells: number;
  critical_count: number;
  watch_count: number;
  stable_count: number;
  unknown_count: number;
  critical_pct: number;
  watch_pct: number;
  stable_pct: number;
  risk_level: string;
  risk_color: string;
  avg_lat: number;
  avg_lon: number;
}

interface StateSummary {
  state: string;
  total_districts: number;
  districts_with_data: number;
  total_wells: number;
  trend_distribution: {
    critical: { count: number; percentage: number };
    watch: { count: number; percentage: number };
    stable: { count: number; percentage: number };
    unknown: { count: number; percentage: number };
  };
  risk_distribution: {
    Critical: number;
    High: number;
    Moderate: number;
    Low: number;
  };
  overall_risk_level: string;
}

const MP_CENTER: [number, number] = [23.47, 77.95];

// Map view controller component
function MapViewController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  
  useEffect(() => {
    map.setView(center, zoom);
  }, [center, zoom, map]);
  
  return null;
}

export default function StressMap({
  onDistrictSelect,
}: {
  onDistrictSelect?: (district: string) => void;
}) {
  const [districts, setDistricts] = useState<DistrictStress[]>([]);
  const [summary, setSummary] = useState<StateSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDistrict, setSelectedDistrict] = useState<string | null>(null);

  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    
    Promise.all([
      fetch(`${API_BASE}/api/v1/stress-map/districts?min_wells=5`).then(r => r.json()),
      fetch(`${API_BASE}/api/v1/stress-map/summary`).then(r => r.json())
    ])
      .then(([districtsData, summaryData]) => {
        setDistricts(districtsData);
        setSummary(summaryData);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  const handleDistrictClick = (district: DistrictStress) => {
    setSelectedDistrict(district.district);
    if (onDistrictSelect) {
      onDistrictSelect(district.district);
    }
  };

  // Calculate marker size based on total wells
  const getMarkerSize = (totalWells: number) => {
    return Math.min(Math.max(totalWells / 5, 15), 40);
  };

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      {error && (
        <div style={{ padding: 8, background: "#fee2e2", color: "#991b1b" }}>
          Could not load stress map: {error}
        </div>
      )}
      
      {loading && (
        <div style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 1000,
          background: "white",
          padding: "20px",
          borderRadius: "8px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.15)"
        }}>
          Loading stress map...
        </div>
      )}
      
      <MapContainer 
        center={MP_CENTER} 
        zoom={7} 
        style={{ height: "100%", width: "100%", outline: "none" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        
        {/* District markers */}
        {districts.map((d) => (
          <CircleMarker
            key={d.district}
            center={[d.avg_lat, d.avg_lon]}
            radius={getMarkerSize(d.total_wells)}
            pathOptions={{ 
              color: d.risk_color,
              fillColor: d.risk_color,
              fillOpacity: 0.6,
              weight: selectedDistrict === d.district ? 4 : 2
            }}
            eventHandlers={{
              click: (e) => {
                L.DomEvent.stopPropagation(e);
                handleDistrictClick(d);
              },
            }}
          >
            <Popup>
              <div style={{ minWidth: "220px", fontFamily: "system-ui, sans-serif" }}>
                {/* District Name */}
                <div style={{ fontWeight: 700, fontSize: "16px", color: "#111827", marginBottom: "8px" }}>
                  {d.district} District
                </div>

                {/* Risk Level Badge */}
                <div style={{
                  display: "inline-block",
                  padding: "4px 12px",
                  background: d.risk_color,
                  color: "white",
                  borderRadius: "12px",
                  fontSize: "12px",
                  fontWeight: 700,
                  marginBottom: "12px"
                }}>
                  {d.risk_level} Risk
                </div>

                <hr style={{ border: "none", borderTop: "1px solid #e5e7eb", margin: "8px 0" }} />

                {/* Statistics */}
                <div style={{ fontSize: "13px", marginBottom: "8px" }}>
                  <div style={{ fontWeight: 600, color: "#6b7280", marginBottom: "4px" }}>
                    Total Wells: {d.total_wells}
                  </div>
                  
                  {d.critical_count > 0 && (
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
                      <span>🔴 Critical:</span>
                      <span style={{ fontWeight: 600 }}>
                        {d.critical_count} ({d.critical_pct}%)
                      </span>
                    </div>
                  )}
                  
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
                    <span>🟡 Watch:</span>
                    <span style={{ fontWeight: 600 }}>
                      {d.watch_count} ({d.watch_pct}%)
                    </span>
                  </div>
                  
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
                    <span>🟢 Stable:</span>
                    <span style={{ fontWeight: 600 }}>
                      {d.stable_count} ({d.stable_pct}%)
                    </span>
                  </div>
                  
                  {d.unknown_count > 0 && (
                    <div style={{ display: "flex", justifyContent: "space-between", color: "#9ca3af" }}>
                      <span>⚪ Unknown:</span>
                      <span>{d.unknown_count}</span>
                    </div>
                  )}
                </div>

                {/* Click hint */}
                <div style={{ fontSize: "11px", color: "#9ca3af", marginTop: "8px", fontStyle: "italic" }}>
                  Click for detailed district report
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
      
      {/* State Summary Panel */}
      {summary && !loading && (
        <div style={{
          position: "absolute",
          top: "20px",
          right: "10px",
          background: "white",
          padding: "16px",
          borderRadius: "12px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          fontSize: "13px",
          zIndex: 1000,
          minWidth: "260px",
          maxWidth: "320px"
        }}>
          <div style={{ fontWeight: 700, fontSize: "16px", marginBottom: "12px", color: "#111827" }}>
            {summary.state}
          </div>
          
          {/* Overall Risk Level */}
          <div style={{
            padding: "8px 12px",
            background: summary.overall_risk_level === "Critical" ? "#fef2f2"
              : summary.overall_risk_level === "High" ? "#fffbeb"
              : summary.overall_risk_level === "Moderate" ? "#fef3c7"
              : "#f0fdf4",
            borderRadius: "8px",
            marginBottom: "12px",
            borderLeft: `4px solid ${
              summary.overall_risk_level === "Critical" ? "#dc2626"
              : summary.overall_risk_level === "High" ? "#f59e0b"
              : summary.overall_risk_level === "Moderate" ? "#fbbf24"
              : "#22c55e"
            }`
          }}>
            <div style={{ fontSize: "11px", color: "#6b7280", marginBottom: "2px" }}>Overall Status</div>
            <div style={{ fontWeight: 700, fontSize: "14px", color: "#111827" }}>
              {summary.overall_risk_level} Risk
            </div>
          </div>

          {/* Statistics */}
          <div style={{ marginBottom: "12px" }}>
            <div style={{ fontWeight: 600, marginBottom: "6px", color: "#374151" }}>
              State Statistics
            </div>
            <div style={{ fontSize: "12px", color: "#6b7280" }}>
              <div style={{ marginBottom: "4px" }}>
                📊 {summary.total_wells} wells in {summary.districts_with_data} districts
              </div>
              <div style={{ marginBottom: "4px" }}>
                🔴 {summary.trend_distribution.critical.count} Critical ({summary.trend_distribution.critical.percentage}%)
              </div>
              <div style={{ marginBottom: "4px" }}>
                🟡 {summary.trend_distribution.watch.count} Watch ({summary.trend_distribution.watch.percentage}%)
              </div>
              <div>
                🟢 {summary.trend_distribution.stable.count} Stable ({summary.trend_distribution.stable.percentage}%)
              </div>
            </div>
          </div>

          {/* Risk Distribution */}
          <div>
            <div style={{ fontWeight: 600, marginBottom: "6px", color: "#374151" }}>
              Districts by Risk Level
            </div>
            <div style={{ fontSize: "12px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
                <span>Critical:</span>
                <span style={{ fontWeight: 600, color: "#dc2626" }}>{summary.risk_distribution.Critical}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
                <span>High:</span>
                <span style={{ fontWeight: 600, color: "#f59e0b" }}>{summary.risk_distribution.High}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
                <span>Moderate:</span>
                <span style={{ fontWeight: 600, color: "#fbbf24" }}>{summary.risk_distribution.Moderate}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Low:</span>
                <span style={{ fontWeight: 600, color: "#22c55e" }}>{summary.risk_distribution.Low}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div style={{
        position: "absolute",
        bottom: "20px",
        right: "10px",
        background: "white",
        padding: "12px",
        borderRadius: "8px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        fontSize: "12px",
        zIndex: 1000,
        minWidth: "180px"
      }}>
        <div style={{ fontWeight: 600, marginBottom: "8px", color: "#111827" }}>
          Risk Levels
        </div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: "4px" }}>
          <div style={{ width: "20px", height: "20px", borderRadius: "50%", background: "#dc2626", marginRight: "8px" }}></div>
          <span>Critical (&gt;40% critical or &gt;70% declining)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: "4px" }}>
          <div style={{ width: "20px", height: "20px", borderRadius: "50%", background: "#f59e0b", marginRight: "8px" }}></div>
          <span>High (20-40% critical or 50-70% declining)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: "4px" }}>
          <div style={{ width: "20px", height: "20px", borderRadius: "50%", background: "#fbbf24", marginRight: "8px" }}></div>
          <span>Moderate (10-20% critical)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center" }}>
          <div style={{ width: "20px", height: "20px", borderRadius: "50%", background: "#22c55e", marginRight: "8px" }}></div>
          <span>Low (&lt;10% critical)</span>
        </div>
        <div style={{ marginTop: "8px", fontSize: "10px", color: "#6b7280", fontStyle: "italic" }}>
          Circle size = number of wells
        </div>
      </div>
    </div>
  );
}
