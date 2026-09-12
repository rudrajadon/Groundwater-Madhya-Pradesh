import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Head from "next/head";

// Dynamically import the map to avoid SSR issues
const StressMapComponent = dynamic(() => import("../components/StressMap"), {
  ssr: false,
});

export default function StressMapPage() {
  return (
    <>
      <Head>
        <title>District Stress Map - Madhya Pradesh Groundwater</title>
        <meta
          name="description"
          content="District-level groundwater stress map showing risk levels across Madhya Pradesh"
        />
      </Head>
      <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
        {/* Header */}
        <header
          style={{
            background: "#1e40af",
            color: "white",
            padding: "1rem 2rem",
            boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700 }}>
                Madhya Pradesh Groundwater Stress Map
              </h1>
              <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.875rem", opacity: 0.9 }}>
                District-level Risk Assessment
              </p>
            </div>
            <a
              href="/"
              style={{
                color: "white",
                textDecoration: "none",
                padding: "0.5rem 1rem",
                background: "rgba(255,255,255,0.2)",
                borderRadius: "6px",
                fontSize: "0.875rem",
                fontWeight: 600,
              }}
            >
              ← Back to Main Map
            </a>
          </div>
        </header>

        {/* Map Container */}
        <div style={{ flex: 1, position: "relative" }}>
          <StressMapComponent />
        </div>
      </div>
    </>
  );
}
