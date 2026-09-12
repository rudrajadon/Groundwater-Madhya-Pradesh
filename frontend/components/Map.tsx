import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, GeoJSON, useMapEvents, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { WellSummary, getWells } from "../lib/api";
import { useRouter } from "next/router";

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

function MapInstanceCapture({ onMapReady }: { onMapReady: (map: L.Map) => void }) {
  const map = useMap();
  useEffect(() => {
    onMapReady(map);
  }, [map, onMapReady]);
  return null;
}

function ZoomResponsiveMarkers({ 
  wells, 
  viewMode, 
  onWellSelect,
  selectedWellId 
}: { 
  wells: WellSummary[]; 
  viewMode: "trend" | "geology";
  onWellSelect: (wellId: string, district?: string) => void;
  selectedWellId?: string | null;
}) {
  const router = useRouter();
  const [zoom, setZoom] = useState(7);
  const markerRefs = useRef<{ [key: string]: L.CircleMarker | null }>({});
  
  const map = useMapEvents({
    zoomend: () => {
      setZoom(map.getZoom());
    },
  });

  // Zoom to selected well and open popup when it changes
  useEffect(() => {
    if (selectedWellId) {
      const selectedWell = wells.find(w => w.well_id === selectedWellId);
      if (selectedWell) {
        map.flyTo([selectedWell.lat, selectedWell.lon], Math.max(zoom, 10), {
          duration: 0.8
        });
        
        // Open popup immediately
        const marker = markerRefs.current[selectedWellId];
        if (marker) {
          marker.openPopup();
        }
      }
    } else {
      // Close all popups when no well is selected
      map.closePopup();
    }
  }, [selectedWellId, wells, map, zoom]);

  // Calculate radius based on zoom level
  // Smaller sizes for better visual clarity
  const getRadius = (zoomLevel: number) => {
    if (zoomLevel <= 5) return 2;
    if (zoomLevel <= 6) return 3;
    if (zoomLevel <= 7) return 4;
    if (zoomLevel <= 8) return 5;
    if (zoomLevel <= 9) return 6;
    if (zoomLevel <= 10) return 7;
    if (zoomLevel <= 12) return 8;
    return 10;
  };

  // Calculate border weight based on zoom level
  // Thinner borders when zoomed out for cleaner look
  const getBorderWeight = (zoomLevel: number) => {
    if (zoomLevel <= 7) return 1;
    if (zoomLevel <= 9) return 1.5;
    return 2;
  };

  const radius = getRadius(zoom);
  const borderWeight = getBorderWeight(zoom);

  return (
    <>
      {wells.map((w) => {
        const isSelected = w.well_id === selectedWellId;
        const borderColor = viewMode === "trend" ? trendBorderColor(w.trend_label) : "#d1d5db";
        const fillCol = viewMode === "trend" ? "#d1d5db" : geologyColor(w.geology_type);
        
        return (
          <CircleMarker
            key={w.well_id}
            center={[w.lat, w.lon]}
            radius={radius}
            pathOptions={{ 
              color: isSelected ? "#000" : borderColor,
              fillColor: fillCol,
              fillOpacity: isSelected ? 1 : 0.7,
              weight: isSelected ? Math.min(borderWeight * 2, 3) : borderWeight
            }}
            eventHandlers={{
              click: (e) => {
                L.DomEvent.stopPropagation(e);
                onWellSelect(w.well_id, w.district || undefined);
              },
              popupclose: (e) => {
                // When popup closes, clear the selection by selecting empty string
                if (isSelected) {
                  onWellSelect('', undefined);
                }
              },
            }}
            ref={(ref) => {
              markerRefs.current[w.well_id] = ref;
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

                {/* Detailed Analysis Button - Mobile Only */}
                <div
                  className="mobile-detailed-analysis-btn"
                  style={{
                    display: "block",
                    marginTop: "10px",
                  }}
                >
                  <a
                    href={`/well/${w.well_id}`}
                    style={{
                      display: "block",
                      padding: "8px 12px",
                      background: "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",
                      color: "white",
                      textDecoration: "none",
                      borderRadius: "6px",
                      fontSize: "12px",
                      fontWeight: 600,
                      textAlign: "center",
                      boxShadow: "0 2px 4px rgba(59, 130, 246, 0.3)",
                    }}
                  >
                    📊 Detailed Analysis
                  </a>
                </div>

                {/* Click hint - Desktop Only */}
                <div className="desktop-click-hint" style={{ fontSize: "11px", color: "#9ca3af", marginTop: "8px", fontStyle: "italic" }}>
                  Click marker for 12-month forecast
                </div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
}

export default function GroundwaterMap({
  onWellSelect,
  onLocationSelect,
  zoomToDistrict,
  selectedWellId,
}: {
  onWellSelect: (wellId: string, district?: string) => void;
  onLocationSelect?: (lat: number, lon: number) => void;
  zoomToDistrict?: string | null;
  selectedWellId?: string | null;
}) {
  const [wells, setWells] = useState<WellSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"trend" | "geology">("trend");
  const [showDistricts, setShowDistricts] = useState<boolean>(true);
  const [districtBoundaries, setDistrictBoundaries] = useState<any>(null);
  const [mapInstance, setMapInstance] = useState<L.Map | null>(null);
  const [legendMinimized, setLegendMinimized] = useState(false);

  useEffect(() => {
    console.log('[Map] Fetching wells data...');
    getWells()
      .then((data) => {
        console.log('[Map] Received wells:', data.length);
        console.log('[Map] Sample well:', data[0]);
        setWells(data);
      })
      .catch((e) => setError(e.message));
  }, []);

  // Load district boundaries
  useEffect(() => {
    console.log('[Map] Fetching district boundaries...');
    const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
    fetch(`${basePath}/geo/mp_districts_simplified.geojson`)
      .then(res => res.json())
      .then(data => {
        console.log('[Map] Loaded district boundaries:', data.features?.length, 'districts');
        setDistrictBoundaries(data);
      })
      .catch(e => console.error('[Map] Failed to load district boundaries:', e));
  }, []);

  // Zoom to district when selected
  useEffect(() => {
    if (zoomToDistrict && districtBoundaries && mapInstance) {
      const feature = districtBoundaries.features.find(
        (f: any) => f.properties?.district?.toUpperCase() === zoomToDistrict.toUpperCase()
      );
      if (feature && feature.geometry) {
        const layer = L.geoJSON(feature);
        const bounds = layer.getBounds();
        mapInstance.fitBounds(bounds, { padding: [50, 50], maxZoom: 11 });
      }
    }
  }, [zoomToDistrict, districtBoundaries, mapInstance]);

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
        zoomControl={true}
        touchZoom={true}
        doubleClickZoom={true}
        scrollWheelZoom={true}
        dragging={true}
      >
        <MapInstanceCapture onMapReady={setMapInstance} />
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        
        {/* District Boundaries Layer */}
        {showDistricts && districtBoundaries && (
          <GeoJSON
            data={districtBoundaries}
            style={() => ({
              color: '#4b5563',        // gray-600
              weight: 2,
              fillOpacity: 0,
              opacity: 0.6
            })}
            onEachFeature={(feature, layer) => {
              if (feature.properties && feature.properties.district) {
                layer.bindTooltip(feature.properties.district, {
                  permanent: false,
                  direction: 'center',
                  className: 'district-label'
                });
              }
            }}
          />
        )}
        
        {onLocationSelect && <MapClickHandler onMapClick={onLocationSelect} />}
        
        {/* Zoom-responsive well markers */}
        <ZoomResponsiveMarkers 
          wells={wells}
          viewMode={viewMode}
          onWellSelect={onWellSelect}
          selectedWellId={selectedWellId}
        />
      </MapContainer>
      
      {/* Legend - Compact with minimize/maximize */}
      <div 
        className={`map-legend ${legendMinimized ? 'minimized' : ''}`}
        style={{
          position: "absolute",
          bottom: "20px",
          right: "20px",
          background: "white",
          padding: legendMinimized ? "8px" : "12px",
          borderRadius: "10px",
          boxShadow: "0 2px 10px rgba(0,0,0,0.15)",
          minWidth: legendMinimized ? "auto" : "200px",
          maxWidth: legendMinimized ? "48px" : "240px",
          zIndex: 400,
        }}
      >
        {legendMinimized ? (
          // Minimized state - just icon button
          <button
            onClick={() => setLegendMinimized(false)}
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              padding: "4px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "24px",
              color: "#374151",
            }}
            aria-label="Expand legend"
            title="Expand legend"
          >
            🗺️
          </button>
        ) : (
          // Expanded state
          <div className="legend-content">
            {/* Compact Header with minimize button */}
            <div style={{ 
              display: "flex", 
              justifyContent: "space-between", 
              alignItems: "center", 
              marginBottom: "8px",
              gap: "6px"
            }}>
              <div style={{ 
                fontSize: "13px", 
                fontWeight: 700, 
                color: "#111827",
                flex: 1
              }}>
                {viewMode === "trend" ? "Trend" : "Geology"}
              </div>
              
              {/* Toggle and Minimize buttons */}
              <div style={{ display: "flex", gap: "3px", alignItems: "center" }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setViewMode(viewMode === "trend" ? "geology" : "trend");
                  }}
                  style={{
                    padding: "2px 6px",
                    background: "#f3f4f6",
                    border: "1px solid #d1d5db",
                    borderRadius: "4px",
                    fontSize: "9px",
                    fontWeight: 600,
                    color: "#374151",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                    lineHeight: 1.2,
                  }}
                  title={`Switch to ${viewMode === "trend" ? "geology" : "trend"} view`}
                >
                  {viewMode === "trend" ? "Geology" : "Trend"}
                </button>
                
                <button
                  onClick={() => setLegendMinimized(true)}
                  style={{
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    padding: "0 3px",
                    fontSize: "18px",
                    color: "#6b7280",
                    lineHeight: 1,
                  }}
                  aria-label="Minimize legend"
                  title="Minimize legend"
                >
                  ×
                </button>
              </div>
            </div>

            {/* District Toggle - Compact */}
            <div className="district-toggle" style={{
              display: "flex",
              alignItems: "center",
              marginBottom: "8px",
              paddingBottom: "6px",
              borderBottom: "1px solid #e5e7eb",
            }}>
              <input
                type="checkbox"
                id="show-districts"
                checked={showDistricts}
                onChange={(e) => setShowDistricts(e.target.checked)}
                style={{ 
                  marginRight: "6px", 
                  cursor: "pointer",
                  width: "14px",
                  height: "14px"
                }}
              />
              <label 
                htmlFor="show-districts" 
                style={{ 
                  fontSize: "11px", 
                  color: "#374151", 
                  cursor: "pointer",
                  userSelect: "none"
                }}
              >
                Districts
              </label>
            </div>

            {/* Legend Items - Compact Grid Layout */}
            <div style={{ 
              display: "grid", 
              gridTemplateColumns: viewMode === "geology" ? "1fr" : "1fr",
              gap: "5px" 
            }}>
              {viewMode === "trend" ? (
                // Trend Legend - Compact
                <>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ 
                      width: "14px", 
                      height: "14px", 
                      borderRadius: "50%", 
                      background: "#d1d5db", 
                      border: "3px solid #ef4444",
                      flexShrink: 0
                    }}></div>
                    <span style={{ fontSize: "11px", color: "#374151" }}>Critical</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ 
                      width: "14px", 
                      height: "14px", 
                      borderRadius: "50%", 
                      background: "#d1d5db", 
                      border: "3px solid #fbbf24",
                      flexShrink: 0
                    }}></div>
                    <span style={{ fontSize: "11px", color: "#374151" }}>Watch</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ 
                      width: "14px", 
                      height: "14px", 
                      borderRadius: "50%", 
                      background: "#d1d5db", 
                      border: "3px solid #22c55e",
                      flexShrink: 0
                    }}></div>
                    <span style={{ fontSize: "11px", color: "#374151" }}>Stable</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ 
                      width: "14px", 
                      height: "14px", 
                      borderRadius: "50%", 
                      background: "#d1d5db", 
                      border: "3px solid #9ca3af",
                      flexShrink: 0
                    }}></div>
                    <span style={{ fontSize: "11px", color: "#374151" }}>Unknown</span>
                  </div>
                </>
              ) : (
                // Geology Legend - Compact with percentages
                <>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ 
                      width: "14px", 
                      height: "14px", 
                      borderRadius: "50%", 
                      background: "#3b82f6",
                      flexShrink: 0
                    }}></div>
                    <span style={{ fontSize: "11px", color: "#374151" }}>
                      Basalt <span className="geology-percent" style={{ color: "#6b7280" }}>({getPercent("Basalt")}%)</span>
                    </span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ 
                      width: "14px", 
                      height: "14px", 
                      borderRadius: "50%", 
                      background: "#a855f7",
                      flexShrink: 0
                    }}></div>
                    <span style={{ fontSize: "11px", color: "#374151" }}>
                      Granite <span className="geology-percent" style={{ color: "#6b7280" }}>({getPercent("Granite")}%)</span>
                    </span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ 
                      width: "14px", 
                      height: "14px", 
                      borderRadius: "50%", 
                      background: "#22c55e",
                      flexShrink: 0
                    }}></div>
                    <span style={{ fontSize: "11px", color: "#374151" }}>
                      Vindhyan <span className="geology-percent" style={{ color: "#6b7280" }}>({getPercent("Vindhyan")}%)</span>
                    </span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <div style={{ 
                      width: "14px", 
                      height: "14px", 
                      borderRadius: "50%", 
                      background: "#9ca3af",
                      flexShrink: 0
                    }}></div>
                    <span style={{ fontSize: "11px", color: "#374151" }}>
                      Unknown <span className="geology-percent" style={{ color: "#6b7280" }}>({getPercent("Unknown")}%)</span>
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
