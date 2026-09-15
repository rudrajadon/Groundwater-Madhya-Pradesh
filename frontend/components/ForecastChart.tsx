import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from "recharts";
import { ForecastPoint } from "../lib/api";

export default function ForecastChart({ 
  forecast, 
  data, 
  darkMode = false, 
  compact = false 
}: { 
  forecast?: ForecastPoint[];
  data?: ForecastPoint[];
  darkMode?: boolean;
  compact?: boolean;
}) {
  const forecastData = forecast || data;
  if (!forecastData) return null;
  const chartData = forecastData.map((p) => ({
    month: `M+${p.month_index}`,
    head: p.head_msl_m,
    lower: p.lower_m,
    upper: p.upper_m,
  }));

  // Calculate Y-axis domain to show variation clearly
  const allValues = forecastData.flatMap(p => [p.head_msl_m, p.lower_m, p.upper_m]);
  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const actualRange = maxValue - minValue;
  
  // Add 20% padding to zoom in tight on the data
  const padding = Math.max(actualRange * 0.2, 1);
  const yMin = Math.floor((minValue - padding) * 10) / 10;
  const yMax = Math.ceil((maxValue + padding) * 10) / 10;

  return (
    <ResponsiveContainer width="100%" height={compact ? 200 : 340}>
      <LineChart data={chartData} margin={{ top: 5, right: compact ? 10 : 20, bottom: compact ? 10 : 20, left: compact ? 5 : 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? "#475569" : "#e2e8f0"} />
        <XAxis 
          dataKey="month" 
          label={compact ? undefined : { 
            value: 'Months Ahead', 
            position: 'insideBottom', 
            offset: -8,
            style: { fontSize: 12, fill: darkMode ? "#94a3b8" : "#64748b" }
          }}
          tick={{ fontSize: compact ? 9 : 11, fill: darkMode ? "#94a3b8" : "#64748b" }}
          stroke={darkMode ? "#475569" : "#cbd5e1"}
        />
        <YAxis 
          domain={[yMin, yMax]}
          scale="linear"
          type="number"
          tickFormatter={(value) => value.toFixed(1)}
          label={compact ? undefined : { 
            value: 'Head MSL (m)', 
            angle: -90, 
            position: 'insideLeft',
            style: { fontSize: 12, fill: darkMode ? "#94a3b8" : "#64748b" }
          }}
          tick={{ fontSize: compact ? 9 : 11, fill: darkMode ? "#94a3b8" : "#64748b" }}
          stroke={darkMode ? "#475569" : "#cbd5e1"}
        />
        <Tooltip 
          formatter={(value: number) => value.toFixed(2) + " m MSL"}
          labelFormatter={(label) => label}
          contentStyle={{
            background: darkMode ? "#1e293b" : "#fff",
            border: darkMode ? "1px solid #475569" : "1px solid #e2e8f0",
            borderRadius: "8px",
            fontSize: compact ? "10px" : "12px",
          }}
        />
        {!compact && (
          <Legend 
            wrapperStyle={{ fontSize: "12px", paddingTop: "15px" }}
            iconType="line"
          />
        )}
        <Line 
          type="monotone" 
          dataKey="upper" 
          name="Upper CI (95%)" 
          stroke="#93c5fd" 
          strokeWidth={compact ? 1 : 1.5} 
          strokeDasharray="5 5"
          dot={false} 
        />
        <Line 
          type="monotone" 
          dataKey="lower" 
          name="Lower CI (95%)" 
          stroke="#93c5fd" 
          strokeWidth={compact ? 1 : 1.5} 
          strokeDasharray="5 5"
          dot={false} 
        />
        <Line 
          type="monotone" 
          dataKey="head" 
          name="Forecast" 
          stroke="#1d4ed8" 
          strokeWidth={compact ? 2 : 3} 
          dot={false} 
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
