import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { WellSummary, getWells } from "../lib/api";

// Madhya Pradesh approximate center
const MP_CENTER: [number, number] = [23.47, 77.95];

function trendBorderColor(label?: string | null): string {
  switch (label) {
    case "Critical": return "#ef4444"; // red
    case "Watch": return "#fbbf24";    // amber
    case "Stable": return "#22c55e";   // green
    default: return "#9ca3af";         // darker gray - unknown/no data
  }
}

function geologyColor(type?: string | null): string {
  switch (type) {
    case "Basalt": return "#3b82f6";    // blue
    case "Granite": return "#a855f7";   // purple
    case "Vindhyan": return "#22c55e";  // green
    default: return "#9ca3af";          // gray - unknown
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
  const [viewMode, setViewMode] = useState<"trend" | "geology">("trend");

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
              color: viewMode === "trend" 
                ? trendBorderColor(w.trend_label)      // Trend mode: colored border
                : "#d1d5db",                           // Geology mode: lighter gray border
              fillColor: viewMode === "trend"
                ? "#d1d5db"                            // Trend mode: lighter gray fill
                : geologyColor(w.geology_type),        // Geology mode: colored fill
              fillOpacity: 0.85,
              weight: 2.5                              // Border thickness
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
      
      {/* Legend with Toggle */}
      <div style={{
        position: "absolute",
        bottom: "20px",
        right: "10px",
        background: "white",
        padding: "16px",
        borderRadius: "12px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        fontSize: "13px",
        zIndex: 1000,
        minWidth: "200px"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <div style={{ fontWeight: 700, color: "#111827", fontSize: "14px" }}>
            {viewMode === "trend" ? "Trend Status" : "Geology Types"}
          </div>
          {/* Compact Toggle Button */}
          <button
            onClick={() => setViewMode(viewMode === "trend" ? "geology" : "trend")}
            style={{
              padding: "4px 10px",
              background: "#f3f4f6",
              border: "1px solid #d1d5db",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 600,
              color: "#374151",
              cursor: "pointer",
              transition: "all 0.2s",
              whiteSpace: "nowrap"
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "#e5e7eb";
              e.currentTarget.style.borderColor = "#9ca3af";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "#f3f4f6";
              e.currentTarget.style.borderColor = "#d1d5db";
            }}
          >
            {viewMode === "trend" ? "Geology" : "Trends"}
          </button>
        </div>

        {viewMode === "trend" ? (
          // Trend Legend
          <>
            <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
              <div style={{ width: "18px", height: "18px", borderRadius: "50%", background: "#d1d5db", border: "3px solid #ef4444", marginRight: "10px" }}></div>
              <span style={{ color: "#374151" }}>Critical</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
              <div style={{ width: "18px", height: "18px", borderRadius: "50%", background: "#d1d5db", border: "3px solid #fbbf24", marginRight: "10px" }}></div>
              <span style={{ color: "#374151" }}>Watch</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
              <div style={{ width: "18px", height: "18px", borderRadius: "50%", background: "#d1d5db", border: "3px solid #22c55e", marginRight: "10px" }}></div>
              <span style={{ color: "#374151" }}>Stable</span>
            </div>
            <div style={{ display: "flex", alignItems: "center" }}>
              <div style={{ width: "18px", height: "18px", borderRadius: "50%", background: "#d1d5db", border: "3px solid #9ca3af", marginRight: "10px" }}></div>
              <span style={{ color: "#374151" }}>Unknown</span>
            </div>
          </>
        ) : (
          // Geology Legend
          <>
            <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
              <div style={{ width: "18px", height: "18px", borderRadius: "50%", background: "#3b82f6", border: "2px solid #d1d5db", marginRight: "10px" }}></div>
              <span style={{ color: "#374151" }}>Basalt ({getPercent("Basalt")}%)</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
              <div style={{ width: "18px", height: "18px", borderRadius: "50%", background: "#a855f7", border: "2px solid #d1d5db", marginRight: "10px" }}></div>
              <span style={{ color: "#374151" }}>Granite ({getPercent("Granite")}%)</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
              <div style={{ width: "18px", height: "18px", borderRadius: "50%", background: "#22c55e", border: "2px solid #d1d5db", marginRight: "10px" }}></div>
              <span style={{ color: "#374151" }}>Vindhyan ({getPercent("Vindhyan")}%)</span>
            </div>
            <div style={{ display: "flex", alignItems: "center" }}>
              <div style={{ width: "18px", height: "18px", borderRadius: "50%", background: "#9ca3af", border: "2px solid #d1d5db", marginRight: "10px" }}></div>
              <span style={{ color: "#374151" }}>Unknown ({getPercent("Unknown")}%)</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
