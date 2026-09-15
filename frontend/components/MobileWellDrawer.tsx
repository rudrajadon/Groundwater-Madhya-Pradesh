import { useEffect, useState } from "react";
import { ForecastResponse } from "../lib/api";
import ForecastChart from "./ForecastChart";
import RainfallChart from "./RainfallChart";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

interface MobileWellDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  pointForecast: ForecastResponse | null;
  history: any[];
  rainfall: any[];
  loading: boolean;
  error: string | null;
  darkMode: boolean;
  onExport: () => void;
}

export default function MobileWellDrawer({
  isOpen,
  onClose,
  pointForecast,
  history,
  rainfall,
  loading,
  error,
  darkMode,
  onExport
}: MobileWellDrawerProps) {
  const [drawerHeight, setDrawerHeight] = useState<'partial' | 'full'>('partial');
  const [startY, setStartY] = useState<number | null>(null);
  const [currentY, setCurrentY] = useState<number | null>(null);
  const [isMobile, setIsMobile] = useState(false);

  // Check if mobile or tablet screen
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 1024);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Reset to partial when opening
  useEffect(() => {
    if (isOpen) {
      setDrawerHeight('partial');
    }
  }, [isOpen]);

  const handleTouchStart = (e: React.TouchEvent) => {
    setStartY(e.touches[0].clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (startY === null) return;
    setCurrentY(e.touches[0].clientY);
  };

  const handleTouchEnd = () => {
    if (startY === null || currentY === null) return;

    const deltaY = currentY - startY;

    // Swipe down - close or go to partial
    if (deltaY > 50) {
      if (drawerHeight === 'full') {
        setDrawerHeight('partial');
      } else {
        onClose();
      }
    }
    // Swipe up - go to full
    else if (deltaY < -50) {
      setDrawerHeight('full');
    }

    setStartY(null);
    setCurrentY(null);
  };

  const historyChartData = history.map((r: any) => ({
    date: r.date,
    head: r.head_msl_m,
    depth: r.depth_bgl_m,
  }));

  // Don't render on desktop (>768px)
  if (!isMobile || !isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="mobile-drawer-backdrop"
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          zIndex: 1500, // Lower than export modal (2000)
          animation: 'fadeIn 0.3s ease-in-out',
        }}
      />

      {/* Drawer */}
      <div
        className={`mobile-well-drawer ${drawerHeight}`}
        style={{
          position: 'fixed',
          left: 0,
          right: 0,
          bottom: 0,
          height: drawerHeight === 'full' ? '90vh' : '60vh',
          background: darkMode ? '#1e293b' : '#ffffff',
          borderTopLeftRadius: '24px',
          borderTopRightRadius: '24px',
          zIndex: 1501, // Lower than export modal (2000)
          boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.3)',
          animation: 'slideUpDrawer 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          transition: 'height 0.3s ease-in-out',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Drag Handle */}
        <div
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          style={{
            width: '100%',
            padding: '12px 0',
            display: 'flex',
            justifyContent: 'center',
            cursor: 'grab',
            flexShrink: 0,
          }}
        >
          <div
            style={{
              width: '48px',
              height: '4px',
              background: darkMode ? '#475569' : '#cbd5e1',
              borderRadius: '2px',
            }}
          />
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: darkMode 
              ? 'linear-gradient(135deg, #475569 0%, #334155 100%)' 
              : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
            border: darkMode ? '1px solid #64748b' : '1px solid #cbd5e1',
            borderRadius: '50%',
            width: '36px',
            height: '36px',
            minWidth: '36px',
            minHeight: '36px',
            padding: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: darkMode ? '#f8fafc' : '#475569',
            zIndex: 10,
            boxShadow: darkMode 
              ? '0 2px 8px rgba(0, 0, 0, 0.3)' 
              : '0 2px 8px rgba(0, 0, 0, 0.1)',
            transition: 'all 0.2s ease',
            flexShrink: 0,
          }}
          onMouseDown={(e) => {
            e.currentTarget.style.transform = 'scale(0.95)';
          }}
          onMouseUp={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = darkMode
              ? 'linear-gradient(135deg, #64748b 0%, #475569 100%)'
              : 'linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%)';
            e.currentTarget.style.boxShadow = darkMode
              ? '0 4px 12px rgba(0, 0, 0, 0.4)'
              : '0 4px 12px rgba(0, 0, 0, 0.15)';
          }}
          aria-label="Close"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>

        {/* Content */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '0 20px 24px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
          }}
        >
          {loading && (
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
            <>
              {/* Well Info Card */}
              <div style={{
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                padding: "20px",
                borderRadius: "16px",
                color: "white",
                boxShadow: "0 10px 25px rgba(102, 126, 234, 0.3)",
              }}>
                <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", opacity: 0.9, marginBottom: 6 }}>
                  Well ID
                </div>
                <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, lineHeight: "1.3", wordBreak: "break-word" }}>
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
                    marginTop: 10,
                    display: "inline-block",
                    background: "rgba(255,255,255,0.2)",
                    padding: "5px 10px",
                    borderRadius: "6px",
                    fontSize: 11,
                    fontWeight: 600,
                  }}>
                    {pointForecast.geology_type}
                  </div>
                )}

                <button
                  onClick={onExport}
                  style={{
                    marginTop: "14px",
                    padding: "10px 16px",
                    background: "rgba(255,255,255,0.95)",
                    color: "#667eea",
                    border: "none",
                    borderRadius: "10px",
                    fontSize: "12px",
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
                >
                  📄 Export Report
                </button>
              </div>

              {/* Trend Status Card */}
              <div style={{
                background: pointForecast.trend_label === "Critical" ? "#fef2f2"
                  : pointForecast.trend_label === "Watch" ? "#fffbeb"
                  : pointForecast.trend_label === "Stable" ? "#f0fdf4" : "#f8fafc",
                padding: "20px",
                borderRadius: "16px",
                border: `2px solid ${
                  pointForecast.trend_label === "Critical" ? "#fecaca"
                  : pointForecast.trend_label === "Watch" ? "#fde68a"
                  : pointForecast.trend_label === "Stable" ? "#bbf7d0" : "#e2e8f0"
                }`
              }}>
                <div style={{
                  fontSize: 10,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "#64748b",
                  marginBottom: 6
                }}>
                  Status
                </div>
                <div style={{
                  fontSize: 24,
                  fontWeight: 800,
                  color: pointForecast.trend_label === "Critical" ? "#dc2626"
                    : pointForecast.trend_label === "Watch" ? "#d97706"
                    : pointForecast.trend_label === "Stable" ? "#16a34a" : "#64748b",
                  marginBottom: 10,
                  letterSpacing: "-0.02em"
                }}>
                  {pointForecast.trend_label}
                </div>
                <p style={{ margin: 0, fontSize: 12, color: "#475569", lineHeight: "1.6" }}>
                  {pointForecast.recommendation}
                </p>
              </div>

              {/* Historical Chart */}
              {history.length > 0 && (
                <div style={{
                  background: darkMode ? "#334155" : "#fff",
                  padding: "20px",
                  borderRadius: "16px",
                  border: darkMode ? "1px solid #475569" : "1px solid #e2e8f0",
                }}>
                  <h4 style={{ margin: "0 0 14px 0", fontSize: 14, fontWeight: 600, color: darkMode ? "#f8fafc" : "#0f172a" }}>
                    Historical Water Levels
                  </h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={historyChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "#475569" : "#e2e8f0"} />
                      <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 10, fill: darkMode ? "#94a3b8" : "#64748b" }}
                        stroke={darkMode ? "#475569" : "#cbd5e1"}
                      />
                      <YAxis 
                        tick={{ fontSize: 10, fill: darkMode ? "#94a3b8" : "#64748b" }}
                        stroke={darkMode ? "#475569" : "#cbd5e1"}
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
                      />
                      <Tooltip 
                        contentStyle={{
                          background: darkMode ? "#1e293b" : "#fff",
                          border: darkMode ? "1px solid #475569" : "1px solid #e2e8f0",
                          borderRadius: "8px",
                          fontSize: 11
                        }}
                      />
                      <Line type="monotone" dataKey="head" stroke="#3b82f6" strokeWidth={2} name="Head (MSL)" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Forecast Chart */}
              {pointForecast.forecast && pointForecast.forecast.length > 0 && (
                <div style={{
                  background: darkMode ? "#334155" : "#fff",
                  padding: "20px",
                  borderRadius: "16px",
                  border: darkMode ? "1px solid #475569" : "1px solid #e2e8f0",
                }}>
                  <h4 style={{ margin: "0 0 14px 0", fontSize: 14, fontWeight: 600, color: darkMode ? "#f8fafc" : "#0f172a" }}>
                    12-Month Forecast
                  </h4>
                  <ForecastChart forecast={pointForecast.forecast} darkMode={darkMode} compact={true} />
                </div>
              )}

              {/* Rainfall Chart */}
              {rainfall.length > 0 && (
                <div style={{
                  background: darkMode ? "#334155" : "#fff",
                  padding: "20px",
                  borderRadius: "16px",
                  border: darkMode ? "1px solid #475569" : "1px solid #e2e8f0",
                }}>
                  <h4 style={{ margin: "0 0 14px 0", fontSize: 14, fontWeight: 600, color: darkMode ? "#f8fafc" : "#0f172a" }}>
                    Rainfall History
                  </h4>
                  <RainfallChart rainfall={rainfall} darkMode={darkMode} compact={true} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
