import { useEffect, useState } from 'react';
import { Marker } from 'react-map-gl/maplibre';
import { FaCircleInfo } from 'react-icons/fa6';

import { DataProduct } from '../../pages/workspace/projects/Project';
import { useRasterSymbologyContext } from '../RasterSymbologyContext';
import { buildLabel } from '../utils';

type SyncPoint = {
  lng: number;
  lat: number;
  originSide: 'left' | 'right';
};

type PointSyncMarkersProps = {
  syncPoint: SyncPoint;
  side: 'left' | 'right';
  dataProduct?: DataProduct | null;
  value?: (number | null)[] | null;
  loading?: boolean;
};

export default function PointSyncMarkers({
  syncPoint,
  side,
  dataProduct,
  value,
  loading = false,
}: PointSyncMarkersProps) {
  const isOrigin = syncPoint.originSide === side;
  const [showPing, setShowPing] = useState(true);
  const { state: symbologyState } = useRasterSymbologyContext();

  // Reset ping animation on each new syncPoint, then stop after 2s
  useEffect(() => {
    setShowPing(true);
    const timer = setTimeout(() => setShowPing(false), 2000);
    return () => clearTimeout(timer);
  }, [syncPoint.lng, syncPoint.lat]);

  const label = buildLabel(value, dataProduct, symbologyState);
  const showLabel = loading || label !== '';

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
        {/* Value label — shown below the dot once values are available */}
        {showLabel && (
          <div className="absolute top-full mt-1.5 left-1/2 -translate-x-1/2 pointer-events-none whitespace-nowrap">
            <div
              className="rounded-lg overflow-hidden"
              style={{ boxShadow: '0 4px 14px rgba(0,0,0,0.18)' }}
            >
              <div
                className="flex items-center gap-1 px-2 py-1"
                style={{
                  backgroundColor: isOrigin ? '#2563eb' : '#ee6c4d',
                  color: 'white',
                }}
              >
                <FaCircleInfo className="w-2.5 h-2.5 shrink-0" />
                <span className="text-[10px] font-semibold tracking-wide uppercase">
                  Pixel Value
                </span>
              </div>
              <div className="px-2 py-1.5 bg-white">
                <span className="text-xs font-medium text-gray-800">
                  {loading ? '…' : label}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </Marker>
  );
}
