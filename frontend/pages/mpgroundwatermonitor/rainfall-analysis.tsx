import { useState, useEffect } from 'react';

interface RainfallData {
  month: string;
  rainfall: number;
  groundwater: number;
}

export default function RainfallAnalysis() {
  const [data, setData] = useState<RainfallData[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Mock data for now
        const mockData: RainfallData[] = Array.from({ length: 12 }, (_, i) => ({
          month: new Date(2024, i).toLocaleString('default', { month: 'short' }),
          rainfall: 50 + Math.random() * 100,
          groundwater: 460 + Math.random() * 10 - 5,
        }));
        setData(mockData);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h1>Rainfall Analysis</h1>
      <p>Rainfall correlation with groundwater levels</p>
      {/* Add chart or table here */}
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
