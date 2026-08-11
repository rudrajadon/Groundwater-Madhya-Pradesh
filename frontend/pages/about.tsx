export default function About() {
  return (
    <div style={{ padding: 24, maxWidth: 800, margin: "0 auto" }}>
      <h1>About — Madhya Pradesh Groundwater Forecast</h1>

      <h2>What is this?</h2>
      <p>
        This app forecasts 12-month groundwater hydraulic head levels for monitoring
        wells across Madhya Pradesh, using a physics-guided graph neural network (PGNN-LSTM)
        trained on real CGWB monitoring data from multiple districts including Indore,
        Jabalpur, Ujjain, Sagar, Bhopal, Guna, and more.
      </p>

      <h2>How it works</h2>
      <ul>
        <li>
          <strong>Model:</strong> PGNN-LSTM v3 — a 2-layer Graph Convolutional Network
          over a 52-well spatial graph, feeding into 4 geology-stratified LSTMs
          (Weathered/Fractured/Massive/Other), with temporal self-attention and a
          12-month forecast head from a 24-month lookback window.
        </li>
        <li>
          <strong>Physics loss:</strong> Custom loss function combining MSE with Darcy
          smoothness, monsoon water-balance, and mass-conservation constraints.
        </li>
        <li>
          <strong>Uncertainty:</strong> Monte Carlo Dropout (30 forward passes) provides
          confidence intervals on every forecast.
        </li>
        <li>
          <strong>GPS lookup:</strong> Click anywhere on the map — if within 2km of a
          monitored well, you get that well's forecast directly. Otherwise, the graph
          is dynamically extended to the new point using distance/geology/block
          edge-weighting.
        </li>
      </ul>

      <h2>Model performance</h2>
      <p>
        The app uses two methods for trend classification:
      </p>
      <ul>
        <li>
          <strong>ML Model (PGNN):</strong> For 300 wells in the training set, uses deep learning
          predictions with 12-month forecast horizon. More accurate but only available for trained wells.
        </li>
        <li>
          <strong>Statistical Analysis:</strong> For all other wells, uses linear regression on
          historical data. Simpler but works for any well with sufficient readings.
        </li>
      </ul>
      <p style={{ background: "#fef3c7", padding: 12, borderRadius: 4, fontSize: 14 }}>
        <strong>Note on map markers:</strong> Border colors on the map show preliminary trends
        based on statistical analysis for quick overview. Click any well to see the detailed
        forecast, which may differ for wells in the ML training set. The detailed forecast
        is always more accurate.
      </p>
      
      <h2>Updated Classification Thresholds (v2)</h2>
      <p>
        Thresholds have been aligned across both ML and statistical methods:
      </p>
      <ul>
        <li><span style={{ color: "#ef4444" }}>●</span> <strong>Critical:</strong> Projected decline ≥ 2.0m over 12 months</li>
        <li><span style={{ color: "#fbbf24" }}>●</span> <strong>Watch:</strong> Projected decline 0.5-2.0m over 12 months</li>
        <li><span style={{ color: "#22c55e" }}>●</span> <strong>Stable:</strong> Decline &lt; 0.5m or improving</li>
      </ul>
      
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
            <th style={{ padding: 8, textAlign: "left" }}>Metric</th>
            <th style={{ padding: 8, textAlign: "left" }}>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: "1px solid #e5e7eb" }}>
            <td style={{ padding: 8 }}>RMSE</td>
            <td style={{ padding: 8 }}>~3.40 m</td>
          </tr>
          <tr style={{ borderBottom: "1px solid #e5e7eb" }}>
            <td style={{ padding: 8 }}>R²</td>
            <td style={{ padding: 8 }}>~0.65</td>
          </tr>
          <tr style={{ borderBottom: "1px solid #e5e7eb" }}>
            <td style={{ padding: 8 }}>Training wells</td>
            <td style={{ padding: 8 }}>300 wells (strategic subset)</td>
          </tr>
          <tr style={{ borderBottom: "1px solid #e5e7eb" }}>
            <td style={{ padding: 8 }}>Total wells</td>
            <td style={{ padding: 8 }}>1,196 wells across MP</td>
          </tr>
          <tr style={{ borderBottom: "1px solid #e5e7eb" }}>
            <td style={{ padding: 8 }}>Forecast horizon</td>
            <td style={{ padding: 8 }}>12 months</td>
          </tr>
        </tbody>
      </table>
      
      <h2>Data sources</h2>
      <ul>
        <li>Well data: 21 MDB files from CGWB covering 18 districts across Madhya Pradesh (1,196 wells with 151,302 readings from 1984-2026)</li>
        <li>Rainfall: Open-Meteo Historical Weather API (ERA5-based)</li>
        <li>Map tiles: OpenStreetMap</li>
      </ul>
      
      <h2>Reliability & Limitations</h2>
      <p>
        This app is designed as a decision support tool, not a definitive prediction system:
      </p>
      <ul>
        <li>Forecasts should be validated with local hydrogeological knowledge</li>
        <li>Wells with limited historical data (&lt;24 months) have higher uncertainty</li>
        <li>Statistical trends assume linear decline - actual behavior may be non-linear</li>
        <li>ML model predictions are only available for 300 trained wells</li>
        <li>Map marker colors provide quick overview but click for accurate forecast</li>
      </ul>
    </div>
  );
}
