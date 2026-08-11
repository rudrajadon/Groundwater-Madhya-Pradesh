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

export default function GroundwaterMap({
  onWellSelect,
}: {
  onWellSelect: (wellId: string) => void;
  onPointSelect?: (lat: number, lon: number) => void;  // Make optional since we won't use it
}) {
  const [wells, setWells] = useState<WellSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getWells()
      .then(setWells)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div style={{ height: "100%", width: "100%", outline: "none" }}>
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
                onWellSelect(w.well_id);
              },
            }}
          >
            <Popup>
              <strong>{w.well_id}</strong>
              <br />
              {w.block}
              {w.aquifer_zone && (
                <>
                  <br />
                  {w.aquifer_zone}
                </>
              )}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
