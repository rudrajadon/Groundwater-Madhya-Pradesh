import { useState, useEffect } from "react";
import { getDistrictStress, DistrictStress } from "../lib/api";

interface DistrictListProps {
  onDistrictClick: (districtName: string) => void;
  selectedDistrict?: string | null;
}

export default function DistrictList({ onDistrictClick, selectedDistrict }: DistrictListProps) {
  const [districts, setDistricts] = useState<DistrictStress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    async function loadDistricts() {
      try {
        const data = await getDistrictStress();
        // Sort by stress score descending (most stressed first)
        const sorted = data.sort((a, b) => b.stress_score - a.stress_score);
        setDistricts(sorted);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    loadDistricts();
  }, []);

  const getDistrictColor = (district: DistrictStress) => {
    if (district.total_wells < 30) return "#9ca3af"; // gray
    if (district.critical_pct >= 20) return "#dc2626"; // red
    if (district.critical_pct >= 12) return "#ea580c"; // red-orange
    if (district.critical_pct >= 8) return "#f97316"; // orange
    if (district.critical_pct >= 5) return "#fb923c"; // light orange
    if (district.watch_pct >= 20) return "#eab308"; // yellow
    if (district.stable_pct >= 80) return "#16a34a"; // green
    return "#84cc16"; // lime (decent)
  };

  const getStatusText = (district: DistrictStress) => {
    if (district.total_wells < 30) return "Insufficient Data";
    if (district.critical_pct >= 20) return "High Stress";
    if (district.critical_pct >= 12) return "Elevated Stress";
    if (district.critical_pct >= 8) return "Moderate Stress";
    if (district.critical_pct >= 5) return "Low Stress";
    if (district.watch_pct >= 20) return "Watch Required";
    if (district.stable_pct >= 80) return "Excellent";
    return "Good";
  };

  if (loading) {
    return (
      <div style={{ padding: 20, textAlign: "center", color: "#6b7280" }}>
        Loading districts...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 16, background: "#fee2e2", color: "#991b1b", borderRadius: 8, fontSize: 14 }}>
        {error}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {/* Dropdown Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          background: "#fff",
          border: "1px solid #e2e8f0",
          borderRadius: "12px",
          padding: "14px 16px",
          cursor: "pointer",
          textAlign: "left",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          transition: "all 0.2s",
          boxShadow: isOpen ? "0 4px 12px rgba(0,0,0,0.08)" : "0 1px 3px rgba(0,0,0,0.02)",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "#cbd5e1";
          e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.08)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "#e2e8f0";
          e.currentTarget.style.boxShadow = isOpen ? "0 4px 12px rgba(0,0,0,0.08)" : "0 1px 3px rgba(0,0,0,0.02)";
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: "#0f172a" }}>
            {selectedDistrict || "All Districts"}
          </span>
          <span style={{ fontSize: 12, color: "#64748b", fontWeight: 500 }}>
            {districts.length} districts available
          </span>
        </div>
        <svg
          width="18"
          height="18"
          viewBox="0 0 16 16"
          fill="none"
          style={{
            transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
            flexShrink: 0,
          }}
        >
          <path
            d="M4 6L8 10L12 6"
            stroke="#64748b"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {/* Dropdown Content */}
      {isOpen && (
        <div
          style={{
            marginTop: 10,
            background: "#fff",
            border: "1px solid #e2e8f0",
            borderRadius: "12px",
            maxHeight: "360px",
            overflowY: "auto",
            boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
          }}
        >
          {districts.map((district, index) => {
            const color = getDistrictColor(district);
            const isSelected = selectedDistrict === district.district;

            return (
              <button
                key={district.district}
                onClick={() => {
                  onDistrictClick(district.district);
                  setIsOpen(false);
                }}
                style={{
                  width: "100%",
                  background: isSelected ? "#eff6ff" : "#fff",
                  border: "none",
                  borderBottom: index < districts.length - 1 ? "1px solid #f1f5f9" : "none",
                  padding: "14px 16px",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "background 0.15s",
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = "#f8fafc";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = "#fff";
                  }
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: district.total_wells >= 30 ? 10 : 0,
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "#0f172a" }}>
                      {district.district}
                    </div>
                    <div style={{ fontSize: 12, color: "#64748b", marginTop: 3 }}>
                      {district.total_wells} wells
                    </div>
                  </div>
                  <div
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: "50%",
                      background: color,
                      flexShrink: 0,
                      marginLeft: 12,
                    }}
                    title={getStatusText(district)}
                  />
                </div>

                {district.total_wells >= 30 && (
                  <div style={{ display: "flex", gap: 10, fontSize: 11 }}>
                    {district.critical_wells > 0 && (
                      <span style={{ color: "#dc2626", fontWeight: 600 }}>
                        {district.critical_wells} Critical
                      </span>
                    )}
                    {district.watch_wells > 0 && (
                      <span style={{ color: "#d97706", fontWeight: 600 }}>
                        {district.watch_wells} Watch
                      </span>
                    )}
                    {district.stable_wells > 0 && (
                      <span style={{ color: "#16a34a", fontWeight: 600 }}>
                        {district.stable_wells} Stable
                      </span>
                    )}
                  </div>
                )}

                {district.total_wells < 30 && (
                  <div
                    style={{
                      fontSize: 11,
                      color: "#94a3b8",
                      fontStyle: "italic",
                      marginTop: 6,
                    }}
                  >
                    Insufficient data
                  </div>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
