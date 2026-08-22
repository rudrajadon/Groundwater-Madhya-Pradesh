import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from "recharts";
import { ForecastPoint } from "../lib/api";

export default function ForecastChart({ data }: { data: ForecastPoint[] }) {
  const chartData = data.map((p) => ({
    month: `M+${p.month_index}`,
    head: p.head_msl_m,
    lower: p.lower_m,
    upper: p.upper_m,
  }));

  // Calculate Y-axis domain to show variation clearly
  const allValues = data.flatMap(p => [p.head_msl_m, p.lower_m, p.upper_m]);
  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const actualRange = maxValue - minValue;
  
  // Add 20% padding to zoom in tight on the data
  const padding = Math.max(actualRange * 0.2, 1);
  const yMin = Math.floor((minValue - padding) * 10) / 10;
  const yMax = Math.ceil((maxValue + padding) * 10) / 10;

  return (
    <ResponsiveContainer width="100%" height={340}>
      <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 20, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis 
          dataKey="month" 
          label={{ 
            value: 'Months Ahead', 
            position: 'insideBottom', 
            offset: -8,
            style: { fontSize: 12, fill: "#64748b" }
          }}
          tick={{ fontSize: 11, fill: "#64748b" }}
          stroke="#cbd5e1"
        />
        <YAxis 
          domain={[yMin, yMax]}
          scale="linear"
          type="number"
          tickFormatter={(value) => value.toFixed(1)}
          label={{ 
            value: 'Head MSL (m)', 
            angle: -90, 
            position: 'insideLeft',
            style: { fontSize: 12, fill: "#64748b" }
          }}
          tick={{ fontSize: 11, fill: "#64748b" }}
          stroke="#cbd5e1"
        />
        <Tooltip 
          formatter={(value: number) => value.toFixed(2) + " m MSL"}
          labelFormatter={(label) => label}
          contentStyle={{
            background: "#fff",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            fontSize: "12px",
          }}
        />
        <Legend 
          wrapperStyle={{ fontSize: "12px", paddingTop: "15px" }}
          iconType="line"
        />
        <Line 
          type="monotone" 
          dataKey="upper" 
          name="Upper CI (95%)" 
          stroke="#93c5fd" 
          strokeWidth={1.5} 
          strokeDasharray="5 5"
          dot={false} 
        />
        <Line 
          type="monotone" 
          dataKey="lower" 
          name="Lower CI (95%)" 
          stroke="#93c5fd" 
          strokeWidth={1.5} 
          strokeDasharray="5 5"
          dot={false} 
        />
        <Line 
          type="monotone" 
          dataKey="head" 
          name="Forecast" 
          stroke="#1d4ed8" 
          strokeWidth={3} 
          dot={false} 
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
