import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { WellSummary, getWells } from "../lib/api";

// Madhya Pradesh approximate center
const MP_CENTER: [number, number] = [23.47, 77.95];

function trendBorderColor(label?: string | null): string {
  switch (label) {
    case "Critical": return "#ef4444"; // lighter red
    case "Watch": return "#fbbf24";    // lighter amber
    case "Stable": return "#22c55e";   // lighter green
    default: return "#d1d5db";         // lighter gray - unknown/no data
  }
}

function MapClickHandler({ onMapClick }: { onMapClick: (lat: number, lon: number) => void }) {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function GroundwaterMap({
  onWellSelect,
  onLocationSelect,
}: {
  onWellSelect: (wellId: string, district?: string) => void;
  onLocationSelect?: (lat: number, lon: number) => void;
}) {
  const [wells, setWells] = useState<WellSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getWells()
      .then(setWells)
      .catch((e) => setError(e.message));
  }, []);

  // Calculate geology distribution percentages
  const geologyStats = wells.reduce((acc, w) => {
    const type = w.geology_type || "Unknown";
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const total = wells.length;
  const getPercent = (type: string) => 
    total > 0 ? ((geologyStats[type] || 0) / total * 100).toFixed(1) : "0.0";

  return (
    <div style={{ height: "100%", width: "100%", outline: "none", position: "relative" }}>
      {error && (
        <div style={{ padding: 8, background: "#fee2e2", color: "#991b1b" }}>
          Could not load wells: {error}. Is the backend running and reachable
          at NEXT_PUBLIC_API_BASE?
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
        {onLocationSelect && <MapClickHandler onMapClick={onLocationSelect} />}
        {wells.map((w) => (
          <CircleMarker
            key={w.well_id}
            center={[w.lat, w.lon]}
            radius={8}
            pathOptions={{ 
              color: trendBorderColor(w.trend_label),  // Lighter colored border
              fillColor: "#9ca3af",                     // Darker gray fill
              fillOpacity: 0.8,
              weight: 2                                 // Border thickness
            }}
            eventHandlers={{
              click: (e) => {
                L.DomEvent.stopPropagation(e);
                onWellSelect(w.well_id, w.district || undefined);
              },
            }}
          >
          <Popup>
              <div style={{ minWidth: "160px", fontFamily: "system-ui, sans-serif" }}>
                {/* Well ID */}
                <div style={{ fontWeight: 700, fontSize: "14px", color: "#111827", marginBottom: "4px" }}>
                  {w.well_id}
                </div>

                {/* Block */}
                {w.block && (
                  <div style={{ fontSize: "12px", color: "#6b7280", marginBottom: "8px" }}>
                    📍 {w.block}
                  </div>
                )}

                <hr style={{ border: "none", borderTop: "1px solid #e5e7eb", margin: "6px 0" }} />

                {/* Geology */}
                {w.geology_type && w.geology_type !== "Unknown" && (
                  <div style={{ fontSize: "12px", marginBottom: "4px" }}>
                    <span style={{ color: "#6b7280" }}>🪨 Rock: </span>
                    <span style={{ fontWeight: 600, color: "#1d4ed8" }}>{w.geology_type}</span>
                  </div>
                )}

                {/* Aquifer */}
                {w.aquifer_classification && w.aquifer_classification !== "Unknown" && (
                  <div style={{ fontSize: "12px", marginBottom: "4px" }}>
                    <span style={{ color: "#6b7280" }}>💧 Aquifer: </span>
                    <span style={{ fontWeight: 600, color: "#0369a1" }}>{w.aquifer_classification}</span>
                  </div>
                )}

                {/* Trend */}
                {w.trend_label && w.trend_label !== "Unknown" && (
                  <div style={{ fontSize: "12px", marginTop: "6px" }}>
                    <span style={{ color: "#6b7280" }}>📊 Trend: </span>
                    <span style={{
                      fontWeight: 700,
                      color: w.trend_label === "Critical" ? "#dc2626"
                           : w.trend_label === "Watch"    ? "#d97706"
                           : "#16a34a"
                    }}>
                      {w.trend_label}
                    </span>
                  </div>
                )}

                {/* Click hint */}
                <div style={{ fontSize: "11px", color: "#9ca3af", marginTop: "8px", fontStyle: "italic" }}>
                  Click marker for 12-month forecast
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
      
      {/* Geology Legend */}
      <div style={{
        position: "absolute",
        bottom: "20px",
        right: "10px",
        background: "white",
        padding: "12px",
        borderRadius: "8px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        fontSize: "13px",
        zIndex: 1000,
        minWidth: "180px"
      }}>
        <div style={{ fontWeight: 600, marginBottom: "8px", color: "#111827" }}>
          Geology Types
        </div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: "4px" }}>
          <div style={{ width: "16px", height: "16px", borderRadius: "50%", background: "#0ea5e9", marginRight: "8px" }}></div>
          <span>Basalt ({getPercent("Basalt")}%)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: "4px" }}>
          <div style={{ width: "16px", height: "16px", borderRadius: "50%", background: "#a855f7", marginRight: "8px" }}></div>
          <span>Granite ({getPercent("Granite")}%)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: "4px" }}>
          <div style={{ width: "16px", height: "16px", borderRadius: "50%", background: "#22c55e", marginRight: "8px" }}></div>
          <span>Vindhyan ({getPercent("Vindhyan")}%)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center" }}>
          <div style={{ width: "16px", height: "16px", borderRadius: "50%", background: "#9ca3af", marginRight: "8px" }}></div>
          <span>Unknown ({getPercent("Unknown")}%)</span>
        </div>
      </div>
    </div>
  );
}
