import dynamic from "next/dynamic";
import { useState, useEffect } from "react";
import { getForecast, getForecastByWellId, getWellHistory, ForecastResponse, getWells, WellSummary } from "../lib/api";
import ForecastChart from "../components/ForecastChart";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";
import LocationPredictor from "../components/LocationPredictor";
import ExportModal from "../components/ExportModal";
import DistrictList from "../components/DistrictList";
import SettingsMenu from "../components/SettingsMenu";
import AgreementModal from "../components/AgreementModal";

const GroundwaterMap = dynamic(() => import("../components/Map"), { ssr: false });
const StressMap = dynamic(() => import("../components/StressMap"), { ssr: false });

export default function Home() {
  const [pointForecast, setPointForecast] = useState<ForecastResponse | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showLocationPredictor, setShowLocationPredictor] = useState(false);
  const [selectedLat, setSelectedLat] = useState<number | undefined>();
  const [selectedLon, setSelectedLon] = useState<number | undefined>();
  const [showExportModal, setShowExportModal] = useState(false);
  const [currentWellId, setCurrentWellId] = useState<string | null>(null);
  const [currentDistrict, setCurrentDistrict] = useState<string | null>(null);
  const [mapView, setMapView] = useState<"wells" | "stress">("wells");
  const [locationPickerMode, setLocationPickerMode] = useState(false);
  const [zoomToDistrict, setZoomToDistrict] = useState<string | null>(null);
  const [districtWells, setDistrictWells] = useState<WellSummary[]>([]);
  const [loadingDistrict, setLoadingDistrict] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [showAgreement, setShowAgreement] = useState(false);

  // Check if user has accepted agreement
  useEffect(() => {
    const hasAccepted = localStorage.getItem('agreementAccepted');
    if (!hasAccepted) {
      setShowAgreement(true);
    }
  }, []);

  // Handle agreement acceptance
  const handleAcceptAgreement = () => {
    localStorage.setItem('agreementAccepted', 'true');
    setShowAgreement(false);
  };

  // Load dark mode preference from localStorage
  useEffect(() => {
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode) {
      setDarkMode(savedMode === 'true');
    }
  }, []);

  // Save dark mode preference to localStorage
  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem('darkMode', newMode.toString());
  };

  async function handleWellSelect(wellId: string, districtName?: string) {
    // If empty wellId, clear selection
    if (!wellId) {
      setPointForecast(null);
      setHistory([]);
      setCurrentWellId(null);
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const [h, fc] = await Promise.all([
        getWellHistory(wellId).catch(e => { console.warn(e); return { readings: [] }; }),
        getForecastByWellId(wellId)
      ]);
      setHistory(h.readings || []);
      setPointForecast(fc);
      setCurrentWellId(wellId);
      setCurrentDistrict(districtName || null);
    } catch (e: any) {
      setError(e.message);
      setPointForecast(null);
      setHistory([]);
      setCurrentWellId(null);
      setCurrentDistrict(null);
    } finally {
      setLoading(false);
    }
  }

  function handleMapClick(lat: number, lon: number) {
    if (locationPickerMode) {
      setSelectedLat(lat);
      setSelectedLon(lon);
      setShowLocationPredictor(true);
    }
  }

  function handleDistrictClick(districtName: string) {
    setCurrentDistrict(districtName);
    setZoomToDistrict(districtName);
    setTimeout(() => setZoomToDistrict(null), 500);
    
    // Load wells for this district
    setLoadingDistrict(true);
    getWells()
      .then(wells => {
        const filtered = wells.filter(w => w.district?.toUpperCase() === districtName.toUpperCase());
        setDistrictWells(filtered);
      })
      .catch(e => console.error('Error loading district wells:', e))
      .finally(() => setLoadingDistrict(false));
  }

  const historyChartData = history.map((r: any) => ({
    date: r.date,
    head: r.head_msl_m,
    depth: r.depth_bgl_m,
  }));

  return (
    <div style={{ display: "flex", height: "100vh", background: darkMode ? "#0f172a" : "#f8fafc" }}>
      {/* Agreement Modal */}
      {showAgreement && <AgreementModal onAccept={handleAcceptAgreement} />}
      
      {/* Settings Menu */}
      <SettingsMenu darkMode={darkMode} onToggleDarkMode={toggleDarkMode} />
      
      {/* Map Section */}
      <div style={{ flex: 1, position: "relative", minWidth: 0 }}>
        
        {/* Header Bar */}
        <div style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
          background: darkMode 
            ? "linear-gradient(to bottom, rgba(15,23,42,0.98), rgba(15,23,42,0.95))"
            : "linear-gradient(to bottom, rgba(255,255,255,0.98), rgba(255,255,255,0.95))",
          backdropFilter: "blur(10px)",
          borderBottom: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
          padding: "16px 24px",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: darkMode ? "#f8fafc" : "#0f172a" }}>
                MP Groundwater Monitor
              </h1>
              <p style={{ margin: "2px 0 0 0", fontSize: 13, color: darkMode ? "#94a3b8" : "#64748b" }}>
                Real-time forecasting & analysis
              </p>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              {/* Custom Location Toggle */}
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 14px",
                background: darkMode ? "#1e293b" : "#fff",
                borderRadius: "8px",
                border: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
              }}>
                <input
                  type="checkbox"
                  id="locationPicker"
                  checked={locationPickerMode}
                  onChange={(e) => setLocationPickerMode(e.target.checked)}
                  style={{
                    cursor: "pointer",
                    width: "18px",
                    height: "18px",
                    accentColor: "#3b82f6",
                  }}
                />
                <label
                  htmlFor="locationPicker"
                  style={{
                    fontSize: "13px",
                    fontWeight: 500,
                    color: darkMode ? "#cbd5e1" : "#475569",
                    cursor: "pointer",
                    userSelect: "none",
                  }}
                >
                  📍 Custom Location
                </label>
              </div>

              {/* Map View Toggle */}
              <div style={{
                display: "flex",
                gap: "6px",
                background: darkMode ? "#1e293b" : "#f1f5f9",
                borderRadius: "10px",
                padding: "4px",
              }}>
                <button
                  onClick={() => setMapView("wells")}
                  style={{
                    padding: "8px 20px",
                    background: mapView === "wells" 
                      ? (darkMode ? "#334155" : "#fff")
                      : "transparent",
                    color: mapView === "wells" 
                      ? (darkMode ? "#f8fafc" : "#0f172a")
                      : (darkMode ? "#94a3b8" : "#64748b"),
                    border: "none",
                    borderRadius: "8px",
                    fontSize: "13px",
                    fontWeight: 600,
                    cursor: "pointer",
                    boxShadow: mapView === "wells" ? "0 2px 4px rgba(0,0,0,0.15)" : "none",
                    transition: "all 0.2s",
                  }}
                >
                  Wells
                </button>
                <button
                  onClick={() => setMapView("stress")}
                  style={{
                    padding: "8px 20px",
                    background: mapView === "stress" 
                      ? (darkMode ? "#334155" : "#fff")
                      : "transparent",
                    color: mapView === "stress" 
                      ? (darkMode ? "#f8fafc" : "#0f172a")
                      : (darkMode ? "#94a3b8" : "#64748b"),
                    border: "none",
                    borderRadius: "8px",
                    fontSize: "13px",
                    fontWeight: 600,
                    cursor: "pointer",
                    boxShadow: mapView === "stress" ? "0 2px 4px rgba(0,0,0,0.15)" : "none",
                    transition: "all 0.2s",
                  }}
                >
                  Stress Map
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Map */}
        <div style={{ height: "100%", paddingTop: "80px" }}>
          {mapView === "wells" ? (
            <GroundwaterMap 
              onWellSelect={handleWellSelect} 
              onLocationSelect={handleMapClick}
              zoomToDistrict={zoomToDistrict}
              selectedWellId={currentWellId}
            />
          ) : (
            <StressMap 
              onDistrictSelect={(district) => setCurrentDistrict(district)} 
              zoomToDistrict={zoomToDistrict}
            />
          )}
        </div>
      </div>
      
      {showLocationPredictor && (
        <LocationPredictor 
          onClose={() => {
            setShowLocationPredictor(false);
            setSelectedLat(undefined);
            setSelectedLon(undefined);
            setLocationPickerMode(false);
          }}
          initialLat={selectedLat}
          initialLon={selectedLon}
        />
      )}
      
      {/* Sidebar */}
      <aside style={{ 
        width: "480px",
        padding: "32px 28px", 
        overflowY: "auto", 
        background: darkMode ? "#1e293b" : "#ffffff",
        borderLeft: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
        display: "flex",
        flexDirection: "column",
        gap: "24px",
      }}>
        
        {/* District Selector - Always visible */}
        {!pointForecast && (
          <div>
            <h3 style={{ 
              margin: "0 0 16px 0", 
              fontSize: 15, 
              fontWeight: 600, 
              color: darkMode ? "#f8fafc" : "#0f172a",
              letterSpacing: "-0.01em" 
            }}>
              Select District
            </h3>
            <DistrictList 
              onDistrictClick={handleDistrictClick}
              selectedDistrict={currentDistrict}
            />
          </div>
        )}

        {/* District Wells List */}
        {!pointForecast && currentDistrict && !loadingDistrict && districtWells.length > 0 && (
          <div style={{ 
            display: "flex", 
            flexDirection: "column",
            flex: 1,
            minHeight: 0,
          }}>
            <div style={{ 
              display: "flex", 
              justifyContent: "space-between", 
              alignItems: "center",
              marginBottom: 16,
              flexShrink: 0,
            }}>
              <h3 style={{ 
                margin: 0, 
                fontSize: 15, 
                fontWeight: 600, 
                color: darkMode ? "#f8fafc" : "#0f172a",
                letterSpacing: "-0.01em" 
              }}>
                Wells in {currentDistrict}
              </h3>
              <span style={{ 
                fontSize: 12, 
                color: darkMode ? "#94a3b8" : "#64748b", 
                fontWeight: 600,
                background: darkMode ? "#334155" : "#f1f5f9",
                padding: "4px 10px",
                borderRadius: "6px"
              }}>
                {districtWells.length} wells
              </span>
            </div>
            
            <div style={{ 
              display: "flex", 
              flexDirection: "column", 
              gap: "8px",
              flex: 1,
              overflowY: "auto",
              minHeight: 0,
            }}>
              {districtWells.map((well) => {
                const trendColor = 
                  well.trend_label === "Critical" ? "#dc2626" :
                  well.trend_label === "Watch" ? "#d97706" :
                  well.trend_label === "Stable" ? "#16a34a" : "#94a3b8";
                
                const geologyColor = 
                  well.geology_type === "Basalt" ? "#3b82f6" :
                  well.geology_type === "Granite" ? "#a855f7" :
                  well.geology_type === "Vindhyan" ? "#22c55e" : "#94a3b8";

                return (
                  <button
                    key={well.well_id}
                    onClick={() => handleWellSelect(well.well_id, well.district)}
                    style={{
                      background: darkMode ? "#334155" : "#fff",
                      border: darkMode ? "1px solid #475569" : "1px solid #e2e8f0",
                      borderRadius: "10px",
                      padding: "12px 14px",
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "all 0.2s",
                      flexShrink: 0,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = darkMode ? "#64748b" : "#cbd5e1";
                      e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.15)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = darkMode ? "#475569" : "#e2e8f0";
                      e.currentTarget.style.boxShadow = "none";
                    }}
                  >
                    <div style={{ 
                      fontSize: 14, 
                      fontWeight: 600, 
                      color: darkMode ? "#f8fafc" : "#0f172a",
                      marginBottom: 8 
                    }}>
                      {well.well_id}
                    </div>
                    
                    <div style={{ 
                      display: "flex", 
                      gap: "10px", 
                      flexWrap: "wrap",
                      alignItems: "center" 
                    }}>
                      {/* Geology Type Badge */}
                      {well.geology_type && well.geology_type !== "Unknown" && (
                        <span style={{
                          fontSize: 11,
                          fontWeight: 600,
                          color: geologyColor,
                          background: `${geologyColor}15`,
                          padding: "3px 8px",
                          borderRadius: "5px",
                          border: `1px solid ${geologyColor}30`,
                        }}>
                          {well.geology_type}
                        </span>
                      )}
                      
                      {/* Trend Badge */}
                      {well.trend_label && well.trend_label !== "Unknown" && (
                        <span style={{
                          fontSize: 11,
                          fontWeight: 600,
                          color: trendColor,
                          background: `${trendColor}15`,
                          padding: "3px 8px",
                          borderRadius: "5px",
                          border: `1px solid ${trendColor}30`,
                        }}>
                          {well.trend_label}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {loadingDistrict && (
          <div style={{ 
            padding: "40px 20px", 
            textAlign: "center",
            color: darkMode ? "#94a3b8" : "#64748b",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "12px"
          }}>
            <div style={{
              width: "40px",
              height: "40px",
              border: `3px solid ${darkMode ? "#334155" : "#e2e8f0"}`,
              borderTopColor: "#3b82f6",
              borderRadius: "50%",
              animation: "spin 0.8s linear infinite",
            }} />
            <div style={{ fontSize: 14, fontWeight: 500 }}>Loading wells...</div>
          </div>
        )}
        
        {loading && (
          <div style={{ 
            padding: "60px 20px", 
            textAlign: "center",
            color: darkMode ? "#94a3b8" : "#64748b",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "12px"
          }}>
            <div style={{
              width: "40px",
              height: "40px",
              border: `3px solid ${darkMode ? "#334155" : "#e2e8f0"}`,
              borderTopColor: "#3b82f6",
              borderRadius: "50%",
              animation: "spin 0.8s linear infinite",
            }} />
            <div style={{ fontSize: 14, fontWeight: 500 }}>Loading well data...</div>
          </div>
        )}
        
        {error && (
          <div style={{ 
            padding: "16px 18px", 
            background: darkMode ? "#7f1d1d" : "#fef2f2", 
            color: darkMode ? "#fecaca" : "#991b1b", 
            borderRadius: "12px", 
            fontSize: 14,
            border: darkMode ? "1px solid #991b1b" : "1px solid #fecaca",
            lineHeight: "1.5"
          }}>
            {error}
          </div>
        )}
        
        {pointForecast && !loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* Back Button */}
            <button
              onClick={() => {
                setPointForecast(null);
                setHistory([]);
                setCurrentWellId(null);
                setCurrentDistrict(null);
              }}
              style={{
                padding: "10px 16px",
                background: darkMode ? "#334155" : "#f1f5f9",
                color: darkMode ? "#cbd5e1" : "#475569",
                border: "none",
                borderRadius: "8px",
                fontSize: "13px",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                width: "fit-content",
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = darkMode ? "#475569" : "#e2e8f0"}
              onMouseLeave={(e) => e.currentTarget.style.background = darkMode ? "#334155" : "#f1f5f9"}
            >
              ← Back to Districts
            </button>

            {/* Well Info Card */}
            <div style={{ 
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", 
              padding: "24px", 
              borderRadius: "16px",
              color: "white",
              boxShadow: "0 10px 25px rgba(102, 126, 234, 0.3)",
            }}>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", opacity: 0.9, marginBottom: 8 }}>
                Well ID
              </div>
              <h3 style={{ margin: 0, fontSize: 20, fontWeight: 700, lineHeight: "1.3" }}>
                {pointForecast.well_id.startsWith('POINT_') ? (
                  (() => {
                    const parts = pointForecast.well_id.replace('POINT_', '').split('_');
                    const lat = parseFloat(parts[0]);
                    const lon = parseFloat(parts[1]);
                    const latDir = lat >= 0 ? 'N' : 'S';
                    const lonDir = lon >= 0 ? 'E' : 'W';
                    return `${Math.abs(lat).toFixed(2)}°${latDir}, ${Math.abs(lon).toFixed(2)}°${lonDir}`;
                  })()
                ) : (
                  pointForecast.well_id
                )}
              </h3>
              {pointForecast.geology_type && (
                <div style={{ 
                  marginTop: 12, 
                  display: "inline-block",
                  background: "rgba(255,255,255,0.2)",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  fontSize: 12,
                  fontWeight: 600,
                }}>
                  {pointForecast.geology_type}
                </div>
              )}
              
              <button
                onClick={() => setShowExportModal(true)}
                style={{
                  marginTop: "16px",
                  padding: "10px 18px",
                  background: "rgba(255,255,255,0.95)",
                  color: "#667eea",
                  border: "none",
                  borderRadius: "10px",
                  fontSize: "13px",
                  fontWeight: 700,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  width: "100%",
                  justifyContent: "center",
                  transition: "all 0.2s",
                  boxShadow: "0 4px 10px rgba(0,0,0,0.15)",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "#fff"}
                onMouseLeave={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.95)"}
              >
                Export Report
              </button>
            </div>

            {/* Trend Status Card */}
            <div style={{ 
              background: pointForecast.trend_label === "Critical" ? "#fef2f2"
                : pointForecast.trend_label === "Watch" ? "#fffbeb"
                : pointForecast.trend_label === "Stable" ? "#f0fdf4" : "#f8fafc",
              padding: "24px", 
              borderRadius: "16px",
              border: `2px solid ${
                pointForecast.trend_label === "Critical" ? "#fecaca"
                : pointForecast.trend_label === "Watch" ? "#fde68a"
                : pointForecast.trend_label === "Stable" ? "#bbf7d0" : "#e2e8f0"
              }`
            }}>
              <div style={{ 
                fontSize: 11, 
                fontWeight: 700, 
                textTransform: "uppercase", 
                letterSpacing: "0.08em", 
                color: "#64748b", 
                marginBottom: 8 
              }}>
                Status
              </div>
              <div style={{ 
                fontSize: 28, 
                fontWeight: 800,
                color: pointForecast.trend_label === "Critical" ? "#dc2626"
                  : pointForecast.trend_label === "Watch" ? "#d97706"
                  : pointForecast.trend_label === "Stable" ? "#16a34a" : "#64748b",
                marginBottom: 12,
                letterSpacing: "-0.02em"
              }}>
                {pointForecast.trend_label}
              </div>
              <p style={{ margin: 0, fontSize: 13, color: "#475569", lineHeight: "1.6" }}>
                {pointForecast.recommendation}
              </p>
            </div>

            {/* Historical Chart - First */}
            {history.length > 0 && (
              <div style={{ 
                background: darkMode ? "#334155" : "#fff", 
                padding: "24px", 
                borderRadius: "16px",
                border: darkMode ? "1px solid #475569" : "1px solid #e2e8f0",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <h4 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: darkMode ? "#f8fafc" : "#0f172a" }}>
                    Historical Water Levels
                  </h4>
                  <span style={{ 
                    fontSize: 11, 
                    color: darkMode ? "#94a3b8" : "#64748b", 
                    fontWeight: 600,
                    background: darkMode ? "#1e293b" : "#f1f5f9",
                    padding: "4px 10px",
                    borderRadius: "6px"
                  }}>
                    {(() => {
                      const dates = history.map((r: any) => new Date(r.date));
                      const oldestDate = new Date(Math.min(...dates.map(d => d.getTime())));
                      const newestDate = new Date(Math.max(...dates.map(d => d.getTime())));
                      const yearsDiff = (newestDate.getTime() - oldestDate.getTime()) / (1000 * 60 * 60 * 24 * 365.25);
                      const years = Math.floor(yearsDiff);
                      
                      return years >= 1 
                        ? `${years} year${years > 1 ? 's' : ''}`
                        : `${history.length} readings`;
                    })()}
                  </span>
                </div>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={historyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "#475569" : "#e2e8f0"} />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 11, fill: darkMode ? "#94a3b8" : "#64748b" }}
                      stroke={darkMode ? "#64748b" : "#cbd5e1"}
                      tickFormatter={(value) => {
                        const date = new Date(value);
                        return `${date.getMonth() + 1}/${date.getFullYear().toString().slice(2)}`;
                      }}
                      label={{ 
                        value: 'Date', 
                        position: 'insideBottom', 
                        offset: -5,
                        style: { fontSize: 12, fill: darkMode ? "#94a3b8" : "#64748b" }
                      }}
                    />
                    <YAxis 
                      tick={{ fontSize: 11, fill: darkMode ? "#94a3b8" : "#64748b" }}
                      stroke={darkMode ? "#64748b" : "#cbd5e1"}
                      domain={[(dataMin: number) => {
                        const values = historyChartData.map(d => d.head).filter(v => v != null);
                        const min = Math.min(...values);
                        const max = Math.max(...values);
                        const range = max - min;
                        const padding = Math.max(range * 0.2, 1);
                        return Math.floor((min - padding) * 10) / 10;
                      }, (dataMax: number) => {
                        const values = historyChartData.map(d => d.head).filter(v => v != null);
                        const min = Math.min(...values);
                        const max = Math.max(...values);
                        const range = max - min;
                        const padding = Math.max(range * 0.2, 1);
                        return Math.ceil((max + padding) * 10) / 10;
                      }]}
                      label={{ 
                        value: 'Head MSL (m)', 
                        angle: -90, 
                        position: 'insideLeft',
                        style: { fontSize: 12, fill: darkMode ? "#94a3b8" : "#64748b" }
                      }}
                    />
                    <Tooltip 
                      contentStyle={{
                        background: darkMode ? "#1e293b" : "#fff",
                        border: darkMode ? "1px solid #475569" : "1px solid #e2e8f0",
                        borderRadius: "8px",
                        fontSize: "12px",
                        color: darkMode ? "#f8fafc" : "#0f172a",
                      }}
                      labelFormatter={(value) => {
                        const date = new Date(value);
                        return date.toLocaleDateString();
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="head" 
                      stroke="#3b82f6" 
                      strokeWidth={2.5}
                      dot={false}
                      name="Head (MSL)" 
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Forecast Chart - Second */}
            <div style={{ 
              background: darkMode ? "#334155" : "#fff", 
              padding: "24px", 
              borderRadius: "16px",
              border: darkMode ? "1px solid #475569" : "1px solid #e2e8f0",
            }}>
              <h4 style={{ margin: "0 0 16px 0", fontSize: 15, fontWeight: 600, color: darkMode ? "#f8fafc" : "#0f172a" }}>
                12-Month Forecast
              </h4>
              <ForecastChart data={pointForecast.forecast} />
            </div>
          </div>
        )}

        {!pointForecast && !loading && !currentDistrict && (
          <div style={{
            padding: "40px 20px",
            textAlign: "center",
            color: darkMode ? "#64748b" : "#94a3b8",
            fontSize: 14,
            lineHeight: "1.6"
          }}>
            <div style={{ fontWeight: 500, color: darkMode ? "#94a3b8" : "#64748b", marginBottom: 6 }}>
              Select a district or well
            </div>
            <div style={{ fontSize: 13 }}>
              Click on the map to view groundwater forecasts
            </div>
          </div>
        )}
      </aside>

      {showExportModal && currentWellId && (
        <ExportModal
          wellId={currentWellId}
          district={currentDistrict || undefined}
          onClose={() => setShowExportModal(false)}
        />
      )}

      <style jsx global>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        
        ::-webkit-scrollbar-track {
          background: #f1f5f9;
        }
        
        ::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </div>
  );
}
