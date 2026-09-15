import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface RainfallData {
  year: number;
  month: number;
  rainfall_mm: number;
  date: string;
}

interface RainfallChartProps {
  rainfall?: RainfallData[];
  data?: RainfallData[];
  darkMode?: boolean;
  compact?: boolean;
}

export default function RainfallChart({ rainfall, data, darkMode = false, compact = false }: RainfallChartProps) {
  const rainfallData = rainfall || data;
  if (!rainfallData || rainfallData.length === 0) {
    return (
      <div className={`p-6 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
        <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
          No rainfall data available
        </p>
      </div>
    );
  }

  // Format data for chart - show last 10 years for better readability
  const currentYear = new Date().getFullYear();
  const recentData = rainfallData.filter(d => d.year >= currentYear - 10);
  
  // Group by year and calculate annual rainfall
  const annualData: { [key: number]: number } = {};
  recentData.forEach(d => {
    if (!annualData[d.year]) {
      annualData[d.year] = 0;
    }
    annualData[d.year] += d.rainfall_mm;
  });
  
  const chartData = Object.entries(annualData).map(([year, rainfall]) => ({
    year: parseInt(year),
    rainfall: Math.round(rainfall),
    label: year
  }));

  // Calculate average for reference line
  const avgRainfall = chartData.reduce((sum, d) => sum + d.rainfall, 0) / chartData.length;

  const textColor = darkMode ? '#d1d5db' : '#374151';
  const gridColor = darkMode ? '#374151' : '#e5e7eb';
  const barColor = darkMode ? '#3b82f6' : '#2563eb';

  return (
    <div className={`${compact ? 'p-0' : 'p-6'} rounded-lg ${darkMode ? 'bg-gray-800' : compact ? '' : 'bg-white'} ${compact ? '' : 'shadow-sm'}`}>
      {!compact && (
        <h3 className={`text-lg font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          Annual Rainfall (Last 10 Years)
        </h3>
      )}
      
      <ResponsiveContainer width="100%" height={compact ? 200 : 300}>
        <BarChart data={chartData} margin={{ top: 5, right: compact ? 10 : 30, left: compact ? 5 : 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
          <XAxis 
            dataKey="label" 
            stroke={textColor}
            tick={{ fill: textColor, fontSize: compact ? 9 : 12 }}
          />
          <YAxis 
            stroke={textColor}
            tick={{ fill: textColor, fontSize: compact ? 9 : 12 }}
            label={compact ? undefined : { 
              value: 'Rainfall (mm)', 
              angle: -90, 
              position: 'insideLeft',
              style: { fill: textColor }
            }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: darkMode ? '#1f2937' : '#ffffff',
              border: `1px solid ${gridColor}`,
              borderRadius: '6px',
              color: textColor,
              fontSize: compact ? '10px' : '12px'
            }}
            formatter={(value: number) => [`${value} mm`, 'Rainfall']}
          />
          {!compact && <Legend />}
          <Bar 
            dataKey="rainfall" 
            fill={barColor} 
            name="Annual Rainfall (mm)"
            radius={[4, 4, 0, 0]}
          />
          <Line 
            type="monotone" 
            dataKey={() => avgRainfall} 
            stroke="#ef4444" 
            strokeDasharray="5 5"
            strokeWidth={compact ? 1.5 : 2}
            dot={false}
            name={`Average (${Math.round(avgRainfall)} mm)`}
          />
        </BarChart>
      </ResponsiveContainer>

      {!compact && (
        <div className={`mt-4 text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          <p>
            <strong>Average annual rainfall:</strong> {Math.round(avgRainfall)} mm
          </p>
        </div>
      )}
    </div>
  );
}
