import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, GeoJSON, Tooltip, useMap, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const MP_CENTER: [number, number] = [23.47, 77.95];

interface DistrictProperties {
  district: string;
  total_wells: number;
  critical_count: number;
  watch_count: number;
  stable_count: number;
  critical_pct: number;
  watch_pct: number;
  stable_pct: number;
  risk_level: string;
  risk_color: string;
}

interface DistrictFeature {
  type: string;
  properties: DistrictProperties;
  geometry: any;
}

interface StressData {
  type: string;
  features: DistrictFeature[];
}

interface StressMapProps {
  onDistrictSelect?: (district: string) => void;
}

interface WellData {
  well_id: string;
  lat: number;
  lon: number;
  trend_label: string;
  district: string;
}

// Component to handle map zoom and bounds
function MapController({ 
  bounds, 
  zoom 
}: { 
  bounds: L.LatLngBoundsExpression | null;
  zoom: number | null;
}) {
  const map = useMap();
  
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
    } else if (zoom) {
      map.setView(MP_CENTER, zoom);
    }
  }, [bounds, zoom, map]);
  
  return null;
}

// Component to capture map instance
function MapInstanceCapture({ onMapReady }: { onMapReady: (map: L.Map) => void }) {
  const map = useMap();
  useEffect(() => {
    onMapReady(map);
  }, [map, onMapReady]);
  return null;
}

// Heat map layer component - creates colored regions based on well locations
// Clipped to district boundaries
function WellHeatMapLayer({ wells, districtGeometry }: { wells: WellData[], districtGeometry?: any }) {
  const map = useMap();
  const layerRef = useRef<any>(null);
  const clipLayerRef = useRef<any>(null);

  console.log(`[WellHeatMapLayer] Rendering with ${wells.length} wells`);

  useEffect(() => {
    if (!map || wells.length === 0) {
      console.log(`[WellHeatMapLayer] Skipping - map: ${!!map}, wells: ${wells.length}`);
      return;
    }

    console.log(`[WellHeatMapLayer] Creating heat circles for ${wells.length} wells`);

    // Remove previous layers
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
    }
    if (clipLayerRef.current) {
      map.removeLayer(clipLayerRef.current);
    }

    // Create the district boundary as a clipping layer
    if (districtGeometry) {
      const districtLayer = L.geoJSON(districtGeometry, {
        style: {
          fill: false,
          color: '#374151',
          weight: 2,
          opacity: 1
        },
        pane: 'overlayPane'
      });
      clipLayerRef.current = districtLayer;
      districtLayer.addTo(map);

      // Function to create/recreate clip path
      const createClipPath = () => {
        const svg = map.getPanes().overlayPane.querySelector('svg');
        if (!svg) return;

        // Create clip path element
        let defs = svg.querySelector('defs');
        if (!defs) {
          defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
          svg.insertBefore(defs, svg.firstChild);
        }

        // Remove old clip path if exists
        const oldClip = defs.querySelector('#district-clip');
        if (oldClip) oldClip.remove();

        // Create new clip path
        const clipPath = document.createElementNS('http://www.w3.org/2000/svg', 'clipPath');
        clipPath.setAttribute('id', 'district-clip');

        // Get the district path and clone it for clipping
        const districtPath = districtLayer.getLayers()[0];
        if (districtPath && (districtPath as any)._path) {
          const pathElement = (districtLayer.getLayers()[0] as any)._path;
          const clonedPath = pathElement.cloneNode(true);
          clipPath.appendChild(clonedPath);
          defs.appendChild(clipPath);
        }
      };

      // Initial clip path creation
      createClipPath();

      // Recreate clip path on zoom/viewreset
      const onMapReset = () => {
        requestAnimationFrame(createClipPath);
      };
      map.on('viewreset', onMapReset);
      map.on('zoomend', onMapReset);

      // Store cleanup function
      (districtLayer as any)._cleanupClipPath = () => {
        map.off('viewreset', onMapReset);
        map.off('zoomend', onMapReset);
      };
    }

    // Group wells by status
    const criticalWells = wells.filter(w => w.trend_label === 'Critical');
    const watchWells = wells.filter(w => w.trend_label === 'Watch');
    const stableWells = wells.filter(w => w.trend_label === 'Stable');

    // Create overlapping circles to form colored regions
    const createHeatCircles = (wellList: WellData[], color: string, opacity: number) => {
      return wellList.map(well => {
        const circle = L.circle([well.lat, well.lon], {
          radius: 3000, // 3km radius of influence
          color: 'transparent',
          fillColor: color,
          fillOpacity: opacity,
          weight: 0,
          interactive: false,
          className: 'heat-circle',
          pane: 'overlayPane'
        });

        // Apply clip path after circle is added
        setTimeout(() => {
          const circleElement = (circle as any)._path;
          if (circleElement && districtGeometry) {
            circleElement.setAttribute('clip-path', 'url(#district-clip)');
          }
        }, 10);

        return circle;
      });
    };

    // Create layers - stable first, then watch, then critical
    const stableCircles = createHeatCircles(stableWells, '#22c55e', 0.25);
    const watchCircles = createHeatCircles(watchWells, '#f59e0b', 0.35);
    const criticalCircles = createHeatCircles(criticalWells, '#dc2626', 0.45);

    // Add all circles to the map in order
    const allCircles = [...stableCircles, ...watchCircles, ...criticalCircles];
    const layerGroup = L.layerGroup(allCircles);
    layerRef.current = layerGroup;
    layerGroup.addTo(map);

    // Apply clip path to all circles after they're rendered
    const applyClipPath = () => {
      allCircles.forEach(circle => {
        const circleElement = (circle as any)._path;
        if (circleElement && districtGeometry) {
          circleElement.setAttribute('clip-path', 'url(#district-clip)');
          circleElement.style.clipPath = 'url(#district-clip)';
        }
      });
    };

    setTimeout(applyClipPath, 100);

    // Reapply clip-path on zoom/pan events (fixes circles breaking during zoom)
    const onMapUpdate = () => {
      requestAnimationFrame(applyClipPath);
    };

    map.on('zoom', onMapUpdate);
    map.on('zoomend', onMapUpdate);
    map.on('moveend', onMapUpdate);
    map.on('viewreset', onMapUpdate);

    return () => {
      map.off('zoom', onMapUpdate);
      map.off('zoomend', onMapUpdate);
      map.off('moveend', onMapUpdate);
      map.off('viewreset', onMapUpdate);
      
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
      }
      if (clipLayerRef.current) {
        // Call stored cleanup function
        if ((clipLayerRef.current as any)._cleanupClipPath) {
          (clipLayerRef.current as any)._cleanupClipPath();
        }
        map.removeLayer(clipLayerRef.current);
      }
      // Clean up clip path
      const panes = map.getPanes();
      if (panes && panes.overlayPane) {
        const svg = panes.overlayPane.querySelector('svg');
        if (svg) {
          const defs = svg.querySelector('defs');
          if (defs) {
            const clipPath = defs.querySelector('#district-clip');
            if (clipPath) clipPath.remove();
          }
        }
      }
    };
  }, [map, wells, districtGeometry]);

  return null;
}

export default function StressMap({ onDistrictSelect, zoomToDistrict }: StressMapProps & { zoomToDistrict?: string | null }) {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  
  const [stressData, setStressData] = useState<StressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDistrict, setSelectedDistrict] = useState<DistrictProperties | null>(null);
  const [districtBounds, setDistrictBounds] = useState<L.LatLngBoundsExpression | null>(null);
  const [currentZoom, setCurrentZoom] = useState<number | null>(7);
  const [districtWells, setDistrictWells] = useState<WellData[]>([]);
  const [showWellLevel, setShowWellLevel] = useState(false);
  const [selectedDistrictGeometry, setSelectedDistrictGeometry] = useState<any>(null);
  const [mapInstance, setMapInstance] = useState<L.Map | null>(null);
  const [legendMinimized, setLegendMinimized] = useState(false);

  useEffect(() => {
    console.log('[StressMap] Loading stress map data...');
    const cacheBuster = Date.now();
    
    // Load district GeoJSON from frontend public folder
    fetch(`/mpgroundwater/geo/mp_districts_simplified.geojson?_=${cacheBuster}`, {
      cache: 'no-store'
    })
      .then(res => res.json())
      .then(geojsonData => {
        console.log('[StressMap] Loaded district GeoJSON:', geojsonData.features?.length, 'districts');
        
        // Now fetch stats from backend
        return fetch(`${API_BASE}/api/v1/stress-map/geojson?min_wells=0&_=${cacheBuster}`, {
          cache: 'no-store'
        })
          .then(res => res.json())
          .then(statsData => {
            console.log('[StressMap] Loaded district stats');
            
            // Merge stats into GeoJSON features
            const districtsStats = statsData.districts || {};
            
            geojsonData.features.forEach((feature: any) => {
              const districtName = feature.properties?.district?.toUpperCase();
              const stats = districtsStats[districtName];
              
              if (stats) {
                // Merge stats into feature properties
                feature.properties = {
                  ...feature.properties,
                  ...stats
                };
              } else {
                // No data for this district
                feature.properties = {
                  ...feature.properties,
                  total_wells: 0,
                  critical_count: 0,
                  watch_count: 0,
                  stable_count: 0,
                  unknown_count: 0,
                  critical_pct: 0.0,
                  watch_pct: 0.0,
                  stable_pct: 0.0,
                  risk_level: "No Data",
                  risk_color: "#d1d5db"
                };
              }
            });
            
            console.log('[StressMap] Merged data, sample:', geojsonData.features[0]?.properties);
            setStressData(geojsonData);
            setLoading(false);
          });
      })
      .catch(e => {
        console.error('[StressMap] Error loading stress data:', e);
        setError(e.message);
        setLoading(false);
      });
  }, []);

  // Zoom to district when selected from sidebar
  useEffect(() => {
    if (zoomToDistrict && stressData && mapInstance) {
      const feature = stressData.features.find(
        (f: any) => f.properties?.district?.toUpperCase() === zoomToDistrict.toUpperCase()
      );
      if (feature && feature.geometry) {
        const layer = L.geoJSON(feature as any);
        const bounds = layer.getBounds();
        mapInstance.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
        
        const props = feature.properties as DistrictProperties;
        
        // Set district state
        setDistrictBounds(bounds);
        setShowWellLevel(props.total_wells >= 30);
        setSelectedDistrictGeometry(feature.geometry);
        
        // Fetch wells for this district if it has enough wells
        if (props.total_wells >= 30) {
          fetch(`${API_BASE}/api/v1/wells?limit=1000`)
            .then(res => res.json())
            .then(wells => {
              const filteredWells = wells.filter((w: WellData) => 
                w.district?.toLowerCase() === props.district?.toLowerCase()
              );
              setDistrictWells(filteredWells);
            })
            .catch(err => console.error('Error fetching wells:', err));
        } else {
          setDistrictWells([]);
        }
        
        setSelectedDistrict(props);
        if (onDistrictSelect) {
          onDistrictSelect(props.district);
        }
      }
    }
  }, [zoomToDistrict, stressData, mapInstance, onDistrictSelect]);

  const getStyle = (feature: any) => {
    const props = feature.properties as DistrictProperties;
    // If district has less than 30 wells, show it in gray (no heat map color)
    const shouldShowHeatMap = props.total_wells >= 30;
    
    if (!shouldShowHeatMap) {
      return {
        fillColor: '#9ca3af',
        fillOpacity: 0.6,
        color: '#374151',
        weight: 1,
        opacity: 1
      };
    }
    
    // Calculate gradient color based on critical and watch percentages
    // Realistic thresholds based on actual groundwater data
    const criticalPct = props.critical_pct;
    const watchPct = props.watch_pct;
    const notStablePct = criticalPct + watchPct;
    
    // Adjusted thresholds:
    // Critical: ≥4% critical OR ≥12% not stable
    // High: 2-4% critical OR 8-12% not stable
    // Moderate: 1-2% critical OR 4-8% not stable
    // Low: <1% critical AND <4% not stable
    
    let fillColor;
    
    if (criticalPct >= 4.0 || notStablePct >= 12.0) {
      // Critical: Soft orange
      fillColor = '#fb923c';
    } else if (criticalPct >= 2.0 || notStablePct >= 8.0) {
      // High: Yellow
      fillColor = '#fbbf24';
    } else if (criticalPct >= 1.0 || notStablePct >= 4.0) {
      // Moderate: Light green
      fillColor = '#86efac';
    } else {
      // Low: Green
      fillColor = '#22c55e';
    }
    
    return {
      fillColor: fillColor,
      fillOpacity: 0.7,
      color: '#374151',
      weight: 1,
      opacity: 1
    };
  };

  const onEachFeature = (feature: any, layer: any) => {
    const props = feature.properties as DistrictProperties;
    
    // Tooltip
    layer.bindTooltip(
      `<div style="font-family: system-ui; font-size: 12px;">
        <strong style="font-size: 14px;">${props.district}</strong><br/>
        ${props.total_wells >= 30
          ? `<span style="color: ${props.risk_color}; font-weight: bold;">${props.risk_level} Risk</span><br/>
             Wells: ${props.total_wells} (${props.critical_count} critical, ${props.watch_count} watch)`
          : props.total_wells > 0
            ? `<span style="color: #6b7280; font-weight: bold;">Insufficient Data (${props.total_wells} wells)</span><br/>
               <span style="font-size: 11px;">Requires ≥30 wells for risk assessment</span>`
            : `<span style="color: #6b7280; font-weight: bold;">No Monitoring Data</span>`
        }
      </div>`,
      { sticky: true }
    );

    // Click handler
    layer.on({
      click: (e: any) => {
        L.DomEvent.stopPropagation(e);
        L.DomEvent.preventDefault(e);
        
        console.log(`[StressMap Click] District: ${props.district}, total_wells: ${props.total_wells}`);
        
        // Calculate bounds of the clicked district
        const bounds = layer.getBounds();
        setDistrictBounds(bounds);
        setShowWellLevel(props.total_wells >= 30);
        
        // Store the district geometry for clipping
        setSelectedDistrictGeometry(feature.geometry);
        
        // Fetch wells for this district if it has enough wells
        if (props.total_wells >= 30) {
          console.log(`[StressMap] Fetching wells for district: ${props.district}`);
          fetch(`${API_BASE}/api/v1/wells?limit=1000`)
            .then(res => {
              console.log(`[StressMap] API response status: ${res.status}`);
              return res.json();
            })
            .then(wells => {
              console.log(`[StressMap] Fetched ${wells.length} total wells`);
              const filteredWells = wells.filter((w: WellData) => 
                w.district?.toLowerCase() === props.district?.toLowerCase()
              );
              console.log(`[StressMap] Filtered to ${filteredWells.length} wells for ${props.district}`);
              setDistrictWells(filteredWells);
            })
            .catch(err => console.error('[StressMap] Error fetching wells:', err));
        } else {
          console.log(`[StressMap] Not enough wells (${props.total_wells}), skipping`);
          setDistrictWells([]);
        }
        
        setSelectedDistrict(props);
        if (onDistrictSelect) {
          onDistrictSelect(props.district);
        }
      },
      mouseover: (e: any) => {
        const layer = e.target;
        layer.setStyle({
          weight: 2,
          fillOpacity: 0.8
        });
      },
      mouseout: (e: any) => {
        const layer = e.target;
        layer.setStyle({
          weight: 1,
          fillOpacity: 0.7
        });
      }
    });
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100%',
        gap: '16px'
      }}>
        <div style={{
          width: '48px',
          height: '48px',
          border: '4px solid #e5e7eb',
          borderTop: '4px solid #667eea',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <div style={{
          fontSize: '1rem',
          color: '#6b7280',
          fontWeight: 500
        }}>
          Loading district stress data...
        </div>
        <style jsx>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100%',
        fontSize: '1rem',
        color: '#dc2626'
      }}>
        Error loading stress map: {error}
      </div>
    );
  }

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      <MapContainer 
        center={MP_CENTER} 
        zoom={7} 
        style={{ height: "100%", width: "100%" }}
        doubleClickZoom={true}
        scrollWheelZoom={true}
        dragging={true}
        zoomControl={true}
        touchZoom={true}
      >
        <MapInstanceCapture onMapReady={setMapInstance} />
        <MapController bounds={districtBounds} zoom={currentZoom} />
        
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        
        {stressData && (
          <GeoJSON
            key={showWellLevel ? 'zoomed' : 'normal'}
            data={stressData as any}
            style={getStyle}
            onEachFeature={onEachFeature}
          />
        )}
        
        {/* Show well-level heat map when zoomed into a district */}
        {showWellLevel && districtWells.length > 0 && (
          <WellHeatMapLayer wells={districtWells} districtGeometry={selectedDistrictGeometry} />
        )}
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
          maxWidth: legendMinimized ? "48px" : "220px",
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
              paddingBottom: "6px",
              borderBottom: "1px solid #e5e7eb"
            }}>
              <div style={{ 
                fontSize: "13px", 
                fontWeight: 700, 
                color: "#111827",
                flex: 1
              }}>
                GW Risk
              </div>
              
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

            {/* Legend Items - Compact */}
            <div style={{ display: "grid", gap: "4px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div style={{ 
                  width: "16px", 
                  height: "14px", 
                  background: "#fb923c", 
                  borderRadius: "2px",
                  flexShrink: 0
                }}></div>
                <span style={{ fontSize: "10px", color: "#374151" }}>Critical (≥4% critical OR ≥12% not stable)</span>
              </div>
              
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div style={{ 
                  width: "16px", 
                  height: "14px", 
                  background: "#fbbf24", 
                  borderRadius: "2px",
                  flexShrink: 0
                }}></div>
                <span style={{ fontSize: "10px", color: "#374151" }}>High (2-4% critical OR 8-12% not stable)</span>
              </div>
              
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div style={{ 
                  width: "16px", 
                  height: "14px", 
                  background: "#86efac", 
                  borderRadius: "2px",
                  flexShrink: 0
                }}></div>
                <span style={{ fontSize: "10px", color: "#374151" }}>Moderate (1-2% critical OR 4-8% not stable)</span>
              </div>
              
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <div style={{ 
                  width: "16px", 
                  height: "14px", 
                  background: "#22c55e", 
                  borderRadius: "2px",
                  flexShrink: 0
                }}></div>
                <span style={{ fontSize: "10px", color: "#374151" }}>Low (&lt;1% critical AND &lt;4% not stable)</span>
              </div>
              
              <div style={{ 
                display: "flex", 
                alignItems: "center", 
                gap: "6px",
                paddingTop: "5px",
                marginTop: "5px",
                borderTop: "1px solid #e5e7eb"
              }}>
                <div style={{ 
                  width: "16px", 
                  height: "14px", 
                  background: "#9ca3af", 
                  borderRadius: "2px",
                  flexShrink: 0
                }}></div>
                <span style={{ fontSize: "10px", color: "#374151" }}>No Data</span>
              </div>
            </div>

            {stressData && (
              <div style={{ 
                marginTop: "8px", 
                paddingTop: "8px", 
                borderTop: "1px solid #e5e7eb", 
                fontSize: "9px", 
                color: "#6b7280",
                textAlign: "center"
              }}>
                {stressData.features.length} districts
              </div>
            )}
          </div>
        )}
      </div>

      {/* District Info Panel */}
      {selectedDistrict && (
        <div 
          className="stress-district-info"
          style={{
            position: "absolute",
            top: "90px", // Increased from 20px to avoid overlapping with fixed navbar
            left: "10px",
            background: "white",
            padding: "20px",
            borderRadius: "12px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            zIndex: 1000,
            minWidth: "300px",
            maxWidth: "400px"
          }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "12px" }}>
            <h3 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 700 }}>
              {selectedDistrict.district}
            </h3>
            <button
              onClick={() => {
                setSelectedDistrict(null);
                setDistrictBounds(null);
                setCurrentZoom(7);
                setShowWellLevel(false);
                setDistrictWells([]);
                setSelectedDistrictGeometry(null);
              }}
              style={{
                background: "none",
                border: "none",
                fontSize: "1.5rem",
                cursor: "pointer",
                color: "#6b7280",
                padding: "0 4px",
                lineHeight: 1
              }}
            >
              ×
            </button>
          </div>

          <div style={{
            display: "inline-block",
            padding: "4px 12px",
            borderRadius: "6px",
            background: selectedDistrict.total_wells >= 30 ? selectedDistrict.risk_color : '#9ca3af',
            color: "white",
            fontWeight: 600,
            fontSize: "0.875rem",
            marginBottom: "16px"
          }}>
            {selectedDistrict.total_wells >= 30 
              ? `${selectedDistrict.risk_level} Risk`
              : selectedDistrict.total_wells > 0
                ? 'Insufficient Data'
                : 'No Data'
            }
          </div>

          {selectedDistrict.total_wells >= 30 ? (
            <>
              <div style={{ fontSize: "0.875rem" }}>
                <div style={{ marginBottom: "8px" }}>
                  <strong>Total Wells:</strong> {selectedDistrict.total_wells}
                </div>
                
                <div style={{ marginBottom: "8px" }}>
                  <strong style={{ color: "#dc2626" }}>Critical:</strong>{" "}
                  {selectedDistrict.critical_count} ({selectedDistrict.critical_pct.toFixed(1)}%)
                </div>
                
                <div style={{ marginBottom: "8px" }}>
                  <strong style={{ color: "#f59e0b" }}>Watch:</strong>{" "}
                  {selectedDistrict.watch_count} ({selectedDistrict.watch_pct.toFixed(1)}%)
                </div>
                
                <div style={{ marginBottom: "8px" }}>
                  <strong style={{ color: "#22c55e" }}>Stable:</strong>{" "}
                  {selectedDistrict.stable_count} ({selectedDistrict.stable_pct.toFixed(1)}%)
                </div>
              </div>
            </>
          ) : selectedDistrict.total_wells > 0 ? (
            <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
              <p><strong>Wells:</strong> {selectedDistrict.total_wells}</p>
              <p style={{ marginTop: "8px" }}>This district has monitoring wells but requires at least 30 wells for reliable risk assessment.</p>
            </div>
          ) : (
            <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
              <p>No monitoring wells currently installed in this district.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
