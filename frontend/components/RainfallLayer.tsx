import { useState, useEffect } from 'react';
import { Circle, Popup } from 'react-leaflet';

interface RainfallLayerProps {
  visible: boolean;
  wells: any[];
}

export default function RainfallLayer({ visible, wells }: RainfallLayerProps) {
  if (!visible) return null;

  return (
    <>
      {wells.map((well) => {
        // Color wells by average rainfall (blue gradient)
        const avgRainfall = well.avg_rainfall || 1000; // mm/year
        const intensity = Math.min(avgRainfall / 1500, 1); // Normalize to 0-1
        const color = `rgba(0, ${Math.floor(100 + 155 * intensity)}, 255, 0.6)`;

        return (
          <Circle
            key={`rainfall-${well.well_id}`}
            center={[well.latitude, well.longitude]}
            radius={8000} // 8km radius
            pathOptions={{ color, fillColor: color, fillOpacity: 0.4 }}
          >
            <Popup>
              <div>
                <strong>{well.well_id}</strong>
                <br />
                Avg Rainfall: {avgRainfall.toFixed(0)} mm/year
              </div>
            </Popup>
          </Circle>
        );
      })}
    </>
  );
}
