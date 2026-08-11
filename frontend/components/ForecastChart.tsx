import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer, Area, ComposedChart } from "recharts";
import { ForecastPoint } from "../lib/api";

export default function ForecastChart({ data }: { data: ForecastPoint[] }) {
  const chartData = data.map((p) => ({
    month: `M+${p.month_index}`,
    head: p.head_msl_m,
    range: [p.lower_m, p.upper_m],
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis label={{ value: "Hydraulic head (m MSL)", angle: -90, position: "insideLeft" }} />
        <Tooltip />
        <Legend />
        <Area dataKey="range" name="Uncertainty band" fill="#93c5fd" stroke="none" />
        <Line type="monotone" dataKey="head" name="Forecast" stroke="#1d4ed8" strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
