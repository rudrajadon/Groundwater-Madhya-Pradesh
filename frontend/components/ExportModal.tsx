import { useState } from "react";

interface ExportModalProps {
  wellId?: string;
  district?: string;
  onClose: () => void;
}

export default function ExportModal({ wellId, district, onClose }: ExportModalProps) {
  const [format, setFormat] = useState<"pdf" | "csv">("pdf");
  const [scope, setScope] = useState<"single" | "district" | "all">(wellId ? "single" : "district");
  const [includeCharts, setIncludeCharts] = useState(true);
  const [reportType, setReportType] = useState<"well" | "district_summary">("well");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  // Auto-switch scope when report type changes
  const handleReportTypeChange = (newReportType: "well" | "district_summary") => {
    setReportType(newReportType);
    
    // If switching to district_summary and we have a district, switch scope
    if (newReportType === "district_summary" && district) {
      setScope("district");
      setFormat("pdf"); // Force PDF for district summary
    }
    // If switching to well and we have a wellId, switch to single
    else if (newReportType === "well" && wellId) {
      setScope("single");
    }
  };

  // Auto-switch to PDF if CSV selected but not single well
  const handleFormatChange = (newFormat: "pdf" | "csv") => {
    if (newFormat === "csv") {
      // Force single well scope and well report type for CSV
      setScope("single");
      setReportType("well");
    }
    setFormat(newFormat);
    setError(null);
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setDownloadUrl(null);

    try {
      // Validate: CSV only for single well
      if (format === "csv" && scope !== "single") {
        setError("CSV export is only available for single well. Please select PDF format for district reports.");
        setLoading(false);
        return;
      }

      const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
      
      console.log('[ExportModal] Generating export:', { API_BASE, scope, district, wellId, format, reportType });
      
      // Build request body
      const requestBody: any = {
        format,
        include_charts: includeCharts,
        report_type: reportType
      };

      if (scope === "single" && wellId) {
        requestBody.well_ids = [wellId];
      } else if (scope === "district" && district) {
        requestBody.district = district;
      } else {
        setError("Please select a well or district to export.");
        setLoading(false);
        return;
      }

      console.log('[ExportModal] Request body:', requestBody);
      console.log('[ExportModal] Fetching:', `${API_BASE}/api/v1/exports/generate`);

      // Create AbortController with 60s timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);

      try {
        const response = await fetch(`${API_BASE}/api/v1/exports/generate`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);
        console.log('[ExportModal] Response status:', response.status, response.statusText);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          console.error('[ExportModal] Error response:', errorData);
          throw new Error(errorData.detail || `Export failed: ${response.statusText}`);
        }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = `groundwater_report_${Date.now()}.${format}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?(.+)"?/);
        if (match) filename = match[1];
      }

      // Convert response to blob
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        setDownloadUrl(url);

        // Auto-download
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          console.error('[ExportModal] Request timeout after 60s');
          throw new Error('Request timed out. The backend may be slow or unavailable.');
        }
        throw fetchError;
      }
    } catch (err: any) {
      console.error('[ExportModal] Export failed:', err);
      setError(err.message || "Failed to generate export");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(0, 0, 0, 0.5)",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      zIndex: 2000,
    }}>
      <div style={{
        background: "#fff",
        borderRadius: "16px",
        boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
        maxWidth: "550px",
        width: "90%",
        maxHeight: "90vh",
        overflow: "auto",
        padding: "24px",
      }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 600, color: "#111827" }}>
              Generate Report
            </h2>
            <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "#6b7280" }}>
              Export groundwater data for analysis
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              fontSize: "24px",
              cursor: "pointer",
              color: "#6b7280",
              padding: "4px 8px",
            }}
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

          {/* Report Type - FIRST */}
          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#111827", marginBottom: "12px" }}>
              Report Type
            </label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "10px" }}>
              {/* Well Forecast Option */}
              <div
                onClick={() => {
                  if (format === "pdf") handleReportTypeChange("well");
                }}
                style={{
                  border: reportType === "well" ? "2px solid #10b981" : "2px solid #e5e7eb",
                  borderRadius: "10px",
                  padding: "14px 16px",
                  cursor: format === "pdf" ? "pointer" : "not-allowed",
                  background: reportType === "well" ? "#ecfdf5" : "#ffffff",
                  transition: "all 0.2s",
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  opacity: format === "csv" ? 0.5 : 1,
                }}
                onMouseEnter={(e) => {
                  if (reportType !== "well" && format === "pdf") e.currentTarget.style.borderColor = "#d1d5db";
                }}
                onMouseLeave={(e) => {
                  if (reportType !== "well" && format === "pdf") e.currentTarget.style.borderColor = "#e5e7eb";
                }}
              >
                <div style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "50%",
                  border: reportType === "well" ? "6px solid #10b981" : "2px solid #d1d5db",
                  flexShrink: 0,
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "#1f2937" }}>
                    Well Forecast Report
                  </div>
                  <div style={{ fontSize: "12px", color: "#6b7280", marginTop: "2px" }}>
                    12-month forecast for single well
                  </div>
                </div>
              </div>

              {/* District Summary Option */}
              <div
                onClick={() => {
                  if (format === "pdf") handleReportTypeChange("district_summary");
                }}
                style={{
                  border: reportType === "district_summary" ? "2px solid #10b981" : "2px solid #e5e7eb",
                  borderRadius: "10px",
                  padding: "14px 16px",
                  cursor: format === "pdf" ? "pointer" : "not-allowed",
                  background: reportType === "district_summary" ? "#ecfdf5" : "#ffffff",
                  transition: "all 0.2s",
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  opacity: format === "csv" ? 0.5 : 1,
                }}
                onMouseEnter={(e) => {
                  if (reportType !== "district_summary" && format === "pdf") e.currentTarget.style.borderColor = "#d1d5db";
                }}
                onMouseLeave={(e) => {
                  if (reportType !== "district_summary" && format === "pdf") e.currentTarget.style.borderColor = "#e5e7eb";
                }}
              >
                <div style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "50%",
                  border: reportType === "district_summary" ? "6px solid #10b981" : "2px solid #d1d5db",
                  flexShrink: 0,
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "#1f2937" }}>
                    District Summary Report
                  </div>
                  <div style={{ fontSize: "12px", color: "#6b7280", marginTop: "2px" }}>
                    Summary of all wells in district
                  </div>
                </div>
              </div>
            </div>
            {format === "csv" && (
              <div style={{
                marginTop: "8px",
                padding: "8px 12px",
                background: "#fef3c7",
                borderRadius: "8px",
                fontSize: "12px",
                color: "#92400e",
              }}>
                Report type selection is only available for PDF format
              </div>
            )}
          </div>

          {/* Data Scope - Display Only */}
          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#111827", marginBottom: "12px" }}>
              Data Scope
            </label>
            <div style={{
              padding: "12px 16px",
              border: "2px solid #e5e7eb",
              borderRadius: "10px",
              background: "#f9fafb",
              fontSize: "14px",
              color: "#1f2937",
              fontWeight: 500,
            }}>
              {scope === "single" && wellId && `Current Well: ${wellId}`}
              {scope === "district" && district && `District: ${district}`}
            </div>
          </div>

          {/* Format Selection - THIRD */}
          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#111827", marginBottom: "12px" }}>
              Export Format
            </label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              {/* PDF Card */}
              <div
                onClick={() => handleFormatChange("pdf")}
                style={{
                  border: format === "pdf" ? "2px solid #3b82f6" : "2px solid #e5e7eb",
                  borderRadius: "10px",
                  padding: "16px",
                  cursor: "pointer",
                  background: format === "pdf" ? "#eff6ff" : "#ffffff",
                  transition: "all 0.2s",
                  boxShadow: format === "pdf" ? "0 4px 6px rgba(59, 130, 246, 0.1)" : "none",
                  textAlign: "center",
                }}
                onMouseEnter={(e) => {
                  if (format !== "pdf") e.currentTarget.style.borderColor = "#d1d5db";
                }}
                onMouseLeave={(e) => {
                  if (format !== "pdf") e.currentTarget.style.borderColor = "#e5e7eb";
                }}
              >
                <div style={{ fontSize: "14px", fontWeight: 600, color: "#1f2937", marginBottom: "4px" }}>
                  PDF
                </div>
                <div style={{ fontSize: "12px", color: "#6b7280" }}>
                  Detailed report
                </div>
              </div>

              {/* CSV Card - Only show for single well */}
              {wellId && scope === "single" && reportType === "well" ? (
                <div
                  onClick={() => handleFormatChange("csv")}
                  style={{
                    border: format === "csv" ? "2px solid #3b82f6" : "2px solid #e5e7eb",
                    borderRadius: "10px",
                    padding: "16px",
                    cursor: "pointer",
                    background: format === "csv" ? "#eff6ff" : "#ffffff",
                    transition: "all 0.2s",
                    boxShadow: format === "csv" ? "0 4px 6px rgba(59, 130, 246, 0.1)" : "none",
                    textAlign: "center",
                  }}
                  onMouseEnter={(e) => {
                    if (format !== "csv") e.currentTarget.style.borderColor = "#d1d5db";
                  }}
                  onMouseLeave={(e) => {
                    if (format !== "csv") e.currentTarget.style.borderColor = "#e5e7eb";
                  }}
                >
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "#1f2937", marginBottom: "4px" }}>
                    CSV
                  </div>
                  <div style={{ fontSize: "12px", color: "#6b7280" }}>
                    Raw data
                  </div>
                </div>
              ) : (
                <div
                  style={{
                    border: "2px solid #f3f4f6",
                    borderRadius: "10px",
                    padding: "16px",
                    background: "#f9fafb",
                    opacity: 0.5,
                    textAlign: "center",
                  }}
                >
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "#9ca3af", marginBottom: "4px" }}>
                    CSV
                  </div>
                  <div style={{ fontSize: "12px", color: "#9ca3af" }}>
                    Single well only
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              padding: "12px",
              background: "#fee2e2",
              color: "#991b1b",
              borderRadius: "8px",
              fontSize: "13px",
            }}>
              {error}
            </div>
          )}

          {/* Success Message */}
          {downloadUrl && !error && (
            <div style={{
              padding: "12px",
              background: "#d1fae5",
              color: "#065f46",
              borderRadius: "8px",
              fontSize: "13px",
            }}>
              Report generated successfully!
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ display: "flex", gap: "12px", marginTop: "4px" }}>
            <button
              onClick={handleGenerate}
              disabled={loading}
              style={{
                flex: 1,
                padding: "12px",
                background: loading ? "#e5e7eb" : "#10b981",
                color: "#fff",
                border: "none",
                borderRadius: "8px",
                fontSize: "14px",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Generating..." : "Generate Report"}
            </button>
            <button
              onClick={onClose}
              style={{
                padding: "12px 24px",
                background: "#fff",
                color: "#374151",
                border: "1px solid #d1d5db",
                borderRadius: "8px",
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
