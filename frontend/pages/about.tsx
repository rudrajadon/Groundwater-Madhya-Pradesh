import { useState, useEffect } from "react";
import SettingsMenu from "../components/SettingsMenu";

export default function About() {
  const [darkMode, setDarkMode] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode) {
      setDarkMode(savedMode === 'true');
    }
  }, []);

  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem('darkMode', newMode.toString());
  };

  return (
    <div style={{ 
      minHeight: "100vh", 
      background: darkMode ? "#0f172a" : "#f8fafc",
    }}>
      <SettingsMenu 
        darkMode={darkMode} 
        onToggleDarkMode={toggleDarkMode}
        isOpen={settingsOpen}
        onToggle={setSettingsOpen}
      />

      {/* Header */}
      <div className="header-bar" style={{
        position: "fixed",
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
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {/* IIT Indore Logo */}
            <img 
              src={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/iiti.png`}
              alt="IIT Indore" 
              style={{ 
                height: "40px", 
                width: "auto",
                objectFit: "contain"
              }}
            />
            
            <div>
              <h1 className="header-title" style={{ margin: 0, fontSize: 20, fontWeight: 700, color: darkMode ? "#f8fafc" : "#0f172a" }}>
                <span className="title-full">MP Groundwater Monitor</span>
                <span className="title-short" style={{ display: 'none' }}>MP Groundwater</span>
              </h1>
              <p className="header-subtitle" style={{ margin: "2px 0 0 0", fontSize: 13, color: darkMode ? "#94a3b8" : "#64748b" }}>
                About this project
              </p>
            </div>
          </div>

          <div className="header-controls" style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {/* Settings Button - Right corner on mobile */}
            <button
              onClick={() => {
                setSettingsOpen(!settingsOpen);
              }}
              className="header-settings-btn"
              aria-label="Settings"
              style={{
                display: 'none',
                padding: '10px',
                background: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.9)',
                border: darkMode ? '1px solid rgba(255, 255, 255, 0.2)' : '1px solid rgba(0, 0, 0, 0.1)',
                borderRadius: '8px',
                cursor: 'pointer',
                color: darkMode ? '#e2e8f0' : '#475569',
                minWidth: '44px',
                minHeight: '44px',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = darkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(255, 255, 255, 1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.9)';
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="about-content" style={{
        maxWidth: "1200px",
        margin: "0 auto",
        padding: "48px 24px",
        paddingTop: "120px", // 72px navbar + 48px gap
      }}>
        
        {/* Hero */}
        <div style={{ textAlign: "center", marginBottom: "64px" }}>
          <h2 className="about-hero-title" style={{
            fontSize: "48px",
            fontWeight: 800,
            color: darkMode ? "#f8fafc" : "#0f172a",
            marginBottom: "16px",
            letterSpacing: "-0.03em",
          }}>
            AI-Powered Groundwater Intelligence
          </h2>
          <p className="about-hero-subtitle" style={{
            fontSize: "20px",
            color: darkMode ? "#94a3b8" : "#64748b",
            maxWidth: "700px",
            margin: "0 auto",
            lineHeight: "1.6",
          }}>
            Monitoring and forecasting groundwater levels across Madhya Pradesh using machine learning
          </p>
        </div>

        {/* Overview */}
        <div className="about-card" style={{
          background: darkMode ? "#1e293b" : "white",
          borderRadius: "16px",
          padding: "48px",
          marginBottom: "32px",
          border: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
        }}>
          <h3 className="about-section-title" style={{
            fontSize: "28px",
            fontWeight: 700,
            color: darkMode ? "#f8fafc" : "#0f172a",
            marginBottom: "20px",
          }}>
            About the System
          </h3>
          <p style={{
            fontSize: "16px",
            color: darkMode ? "#cbd5e1" : "#475569",
            lineHeight: "1.8",
            marginBottom: "16px",
          }}>
            MP Groundwater Monitor is a comprehensive web-based platform that integrates real-time monitoring data from over 1,082 observation wells across 10+ districts in Madhya Pradesh with advanced artificial intelligence to provide 12-month groundwater level forecasts.
          </p>
          <p style={{
            fontSize: "16px",
            color: darkMode ? "#cbd5e1" : "#475569",
            lineHeight: "1.8",
          }}>
            The platform serves water resource managers, policy makers, researchers, and agricultural planners by offering district-level stress analysis, historical trend visualization, and spatial prediction capabilities for evidence-based groundwater management.
          </p>
        </div>

        {/* Stats */}
        <div className="about-stats-grid" style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "24px",
          marginBottom: "48px",
        }}>
          {[
            { label: "Monitoring Wells", value: "1,082+" },
            { label: "Districts Covered", value: "10+" },
            { label: "Forecast Horizon", value: "12 Months" },
            { label: "Data Source", value: "CGWB" },
          ].map((stat, idx) => (
            <div
              key={idx}
              className="about-stat-card"
              style={{
                background: darkMode ? "#1e293b" : "white",
                padding: "32px",
                borderRadius: "12px",
                textAlign: "center",
                border: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
              }}
            >
              <div className="about-stat-value" style={{
                fontSize: "36px",
                fontWeight: 800,
                color: "#667eea",
                marginBottom: "8px",
              }}>
                {stat.value}
              </div>
              <div className="about-stat-label" style={{
                fontSize: "13px",
                fontWeight: 600,
                color: darkMode ? "#94a3b8" : "#64748b",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Two Column */}
        <div className="about-two-column" style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "32px",
          marginBottom: "48px",
        }}>
          
          {/* Features */}
          <div style={{
            background: darkMode ? "#1e293b" : "white",
            borderRadius: "16px",
            padding: "40px",
            border: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
          }}>
            <h3 style={{
              fontSize: "24px",
              fontWeight: 700,
              color: darkMode ? "#f8fafc" : "#0f172a",
              marginBottom: "24px",
            }}>
              Key Features
            </h3>
            <ul style={{
              listStyle: "none",
              padding: 0,
              margin: 0,
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}>
              {[
                "Interactive map visualization with 1,082+ wells",
                "AI-powered 12-month forecasts with confidence intervals",
                "District-level stress analysis and heat maps",
                "Multi-year historical data and trend analysis",
                "Custom location predictions via interpolation",
                "PDF and CSV report generation",
              ].map((feature, idx) => (
                <li
                  key={idx}
                  style={{
                    fontSize: "15px",
                    color: darkMode ? "#cbd5e1" : "#475569",
                    lineHeight: "1.6",
                    paddingLeft: "24px",
                    position: "relative",
                  }}
                >
                  <span style={{
                    position: "absolute",
                    left: "0",
                    color: "#667eea",
                    fontWeight: "bold",
                  }}>
                    ✓
                  </span>
                  {feature}
                </li>
              ))}
            </ul>
          </div>

          {/* How it Works */}
          <div style={{
            background: darkMode ? "#1e293b" : "white",
            borderRadius: "16px",
            padding: "40px",
            border: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
          }}>
            <h3 style={{
              fontSize: "24px",
              fontWeight: 700,
              color: darkMode ? "#f8fafc" : "#0f172a",
              marginBottom: "24px",
            }}>
              How It Works
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              {[
                { num: "1", title: "Data Collection", desc: "Gather measurements from CGWB and State departments" },
                { num: "2", title: "Spatial Integration", desc: "Integrate geology, aquifer data, and boundaries" },
                { num: "3", title: "ML Forecasting", desc: "PGNN-LSTM generates 12-month predictions" },
                { num: "4", title: "Visualization", desc: "Present insights via interactive maps and charts" },
              ].map((step, idx) => (
                <div key={idx} style={{ display: "flex", gap: "16px" }}>
                  <div style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "50%",
                    background: "#667eea",
                    color: "white",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "16px",
                    fontWeight: "700",
                    flexShrink: 0,
                  }}>
                    {step.num}
                  </div>
                  <div>
                    <div style={{
                      fontSize: "16px",
                      fontWeight: "600",
                      color: darkMode ? "#f8fafc" : "#0f172a",
                      marginBottom: "4px",
                    }}>
                      {step.title}
                    </div>
                    <div style={{
                      fontSize: "14px",
                      color: darkMode ? "#94a3b8" : "#64748b",
                      lineHeight: "1.6",
                    }}>
                      {step.desc}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Technology */}
        <div style={{
          background: darkMode ? "#1e293b" : "white",
          borderRadius: "16px",
          padding: "40px",
          marginBottom: "32px",
          border: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
        }}>
          <h3 className="about-section-title" style={{
            fontSize: "24px",
            fontWeight: 700,
            color: darkMode ? "#f8fafc" : "#0f172a",
            marginBottom: "32px",
          }}>
            Technology Stack
          </h3>
          <div className="about-tech-grid" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "40px" }}>
            {[
              { title: "Frontend", items: ["Next.js 14", "React 18", "TypeScript", "Leaflet.js", "Recharts"] },
              { title: "Backend", items: ["Python 3.11", "FastAPI", "PostgreSQL", "PostGIS", "Docker"] },
              { title: "Machine Learning", items: ["PyTorch", "PGNN + LSTM", "Graph Neural Networks", "scikit-learn"] },
            ].map((stack, idx) => (
              <div key={idx}>
                <h4 style={{
                  fontSize: "14px",
                  fontWeight: 700,
                  color: "#667eea",
                  marginBottom: "16px",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}>
                  {stack.title}
                </h4>
                <ul style={{
                  listStyle: "none",
                  padding: 0,
                  margin: 0,
                  fontSize: "15px",
                  color: darkMode ? "#cbd5e1" : "#64748b",
                  lineHeight: "2",
                }}>
                  {stack.items.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* ML Model */}
        <div style={{
          background: darkMode ? "#1e293b" : "white",
          borderRadius: "16px",
          padding: "40px",
          marginBottom: "32px",
          border: darkMode ? "1px solid #334155" : "1px solid #e2e8f0",
        }}>
          <h3 style={{
            fontSize: "24px",
            fontWeight: 700,
            color: darkMode ? "#f8fafc" : "#0f172a",
            marginBottom: "20px",
          }}>
            Machine Learning Model
          </h3>
          <p style={{
            fontSize: "16px",
            color: darkMode ? "#cbd5e1" : "#475569",
            lineHeight: "1.8",
            marginBottom: "32px",
          }}>
            The forecasting engine uses a hybrid <strong>Position-aware Graph Neural Network (PGNN) + Long Short-Term Memory (LSTM)</strong> architecture that captures both spatial dependencies between wells and temporal patterns in groundwater dynamics.
          </p>
          <div className="about-model-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
            <div style={{
              padding: "24px",
              background: darkMode ? "rgba(220, 38, 38, 0.1)" : "#fef2f2",
              borderRadius: "12px",
              border: darkMode ? "1px solid rgba(220, 38, 38, 0.2)" : "1px solid #fecaca",
            }}>
              <h4 style={{
                fontSize: "18px",
                fontWeight: 600,
                color: darkMode ? "#fca5a5" : "#991b1b",
                marginBottom: "12px",
              }}>
                Spatial Component (PGNN)
              </h4>
              <p style={{
                fontSize: "14px",
                color: darkMode ? "#fca5a5" : "#7f1d1d",
                lineHeight: "1.7",
                margin: 0,
              }}>
                Models inter-well relationships using graph structures, considering distance, geology, aquifer characteristics, and elevation.
              </p>
            </div>
            <div style={{
              padding: "24px",
              background: darkMode ? "rgba(37, 99, 235, 0.1)" : "#eff6ff",
              borderRadius: "12px",
              border: darkMode ? "1px solid rgba(37, 99, 235, 0.2)" : "1px solid #bfdbfe",
            }}>
              <h4 style={{
                fontSize: "18px",
                fontWeight: 600,
                color: darkMode ? "#93c5fd" : "#1e40af",
                marginBottom: "12px",
              }}>
                Temporal Component (LSTM)
              </h4>
              <p style={{
                fontSize: "14px",
                color: darkMode ? "#93c5fd" : "#1e3a8a",
                lineHeight: "1.7",
                margin: 0,
              }}>
                Learns seasonal variations, monsoon impacts, and long-term trends from multi-year historical time series data.
              </p>
            </div>
          </div>
        </div>

        {/* Developer */}
        <div style={{
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          borderRadius: "16px",
          padding: "48px",
          marginBottom: "32px",
          color: "white",
        }}>
          <h3 style={{
            fontSize: "24px",
            fontWeight: 700,
            marginBottom: "32px",
          }}>
            Developer
          </h3>
          
          <div style={{
            marginBottom: "40px",
            paddingBottom: "40px",
            borderBottom: "1px solid rgba(255,255,255,0.2)",
          }}>
            <div className="about-developer-title" style={{
              fontSize: "32px",
              fontWeight: 800,
              marginBottom: "8px",
              letterSpacing: "-0.02em",
            }}>
              Rudra Pratap Singh Jadon
            </div>
            <div className="about-developer-name" style={{
              fontSize: "18px",
              opacity: 0.9,
              marginBottom: "16px",
            }}>
              Full Stack Developer & ML Engineer
            </div>
            <p style={{
              fontSize: "15px",
              lineHeight: "1.7",
              opacity: 0.9,
              maxWidth: "700px",
            }}>
              Specialized in building AI-driven applications for environmental monitoring and resource management with expertise in web technologies and deep learning.
            </p>
          </div>

          <div>
            <h4 style={{
              fontSize: "14px",
              fontWeight: 700,
              marginBottom: "20px",
              opacity: 0.9,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
            }}>
              Under Guidance Of
            </h4>
            <div className="about-guidance-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              <div style={{
                padding: "24px",
                background: "rgba(255,255,255,0.1)",
                borderRadius: "12px",
                backdropFilter: "blur(10px)",
              }}>
                <div style={{
                  fontSize: "20px",
                  fontWeight: 700,
                  marginBottom: "6px",
                }}>
                  Dr. Manish Kumar Goyal
                </div>
                <div style={{
                  fontSize: "15px",
                  opacity: 0.9,
                }}>
                  Professor, IIT Indore
                </div>
              </div>
              <div style={{
                padding: "24px",
                background: "rgba(255,255,255,0.1)",
                borderRadius: "12px",
                backdropFilter: "blur(10px)",
              }}>
                <div style={{
                  fontSize: "20px",
                  fontWeight: 700,
                  marginBottom: "6px",
                }}>
                  Deepak Mishra
                </div>
                <div style={{
                  fontSize: "15px",
                  opacity: 0.9,
                }}>
                  PhD Scholar, IIT Indore
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div style={{
          padding: "32px",
          background: darkMode ? "rgba(245, 158, 11, 0.1)" : "#fffbeb",
          borderRadius: "12px",
          border: darkMode ? "1px solid rgba(245, 158, 11, 0.3)" : "1px solid #fcd34d",
        }}>
          <h4 style={{
            fontSize: "18px",
            fontWeight: 700,
            color: darkMode ? "#fcd34d" : "#92400e",
            marginBottom: "12px",
          }}>
            Important Disclaimer
          </h4>
          <p style={{
            fontSize: "15px",
            color: darkMode ? "#fde68a" : "#78350f",
            lineHeight: "1.7",
            margin: 0,
          }}>
            This system provides forecasts for planning and research purposes only. Actual groundwater conditions may vary due to precipitation, extraction rates, and other factors. Always consult qualified hydrogeologists and water resource experts before making critical decisions.
          </p>
        </div>

        {/* Footer */}
        <div style={{
          textAlign: "center",
          padding: "32px 0",
          color: darkMode ? "#64748b" : "#94a3b8",
          fontSize: "14px",
        }}>
          MP Groundwater Monitor © {new Date().getFullYear()} • Open source for educational purposes
        </div>
      </div>
    </div>
  );
}
