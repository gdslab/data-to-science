import { useEffect, useState } from 'react';
import { Marker } from 'react-map-gl/maplibre';

type SyncPoint = {
  lng: number;
  lat: number;
  originSide: 'left' | 'right';
};

type PointSyncMarkersProps = {
  syncPoint: SyncPoint;
  side: 'left' | 'right';
};

export default function PointSyncMarkers({ syncPoint, side }: PointSyncMarkersProps) {
  const isOrigin = syncPoint.originSide === side;
  const [showPing, setShowPing] = useState(true);

  // Reset ping animation on each new syncPoint, then stop after 2s
  useEffect(() => {
    setShowPing(true);
    const timer = setTimeout(() => setShowPing(false), 2000);
    return () => clearTimeout(timer);
  }, [syncPoint.lng, syncPoint.lat]);

  return (
    <Marker longitude={syncPoint.lng} latitude={syncPoint.lat} anchor="center">
      <div className="relative flex items-center justify-center w-5 h-5">
        {/* Ping ring — only on the target (non-origin) side */}
        {!isOrigin && showPing && (
          <span
            className="absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping"
            style={{ backgroundColor: '#ee6c4d' }}
          />
        )}
        {/* Static dot */}
        <span
          className="relative inline-flex rounded-full w-3 h-3 border-2 border-white shadow"
          style={{ backgroundColor: isOrigin ? '#2563eb' : '#ee6c4d' }}
        />
      </div>
    </Marker>
  );
}
