import { Popup } from 'react-map-gl/maplibre';
import { FaCircleInfo } from 'react-icons/fa6';

import { DataProduct } from '../pages/workspace/projects/Project';
import { useRasterSymbologyContext } from './RasterSymbologyContext';
import { usePointValue, IdentifyPoint } from './usePointValue';
import { buildLabel } from './utils';

type IdentifyPopupProps = {
  dataProduct: DataProduct;
  point: IdentifyPoint;
  onClose: () => void;
};

/**
 * Popup that samples the raster cell value at a clicked point and displays it.
 * - Single-band products show a value with unit (e.g. "187.42 metre").
 * - Multiband/ortho products show R/G/B values matched to the displayed channels.
 * - Points outside the raster footprint or nodata pixels show "No data".
 */
export default function IdentifyPopup({
  dataProduct,
  point,
  onClose,
}: IdentifyPopupProps) {
  const { data, loading, error } = usePointValue(dataProduct, point);
  const { state: symbologyState } = useRasterSymbologyContext();

  let content: string;
  if (loading) {
    content = 'Sampling…';
  } else if (error) {
    content = 'Unable to read value';
  } else {
    content = buildLabel(data?.values ?? null, dataProduct, symbologyState);
  }

  return (
    <Popup
      anchor="top"
      longitude={point.lng}
      latitude={point.lat}
      onClose={onClose}
      closeOnClick={false}
      maxWidth="240px"
      className="identify-popup"
    >
      <div>
        <div
          className="flex items-center gap-1.5 px-3 py-1.5 pr-7"
          style={{ backgroundColor: 'var(--color-primary)', color: 'white' }}
        >
          <FaCircleInfo className="w-3 h-3 shrink-0" />
          <span className="text-xs font-semibold tracking-wide uppercase">
            Pixel Value
          </span>
        </div>
        <div className="px-3 py-2 bg-white">
          <p className="text-sm font-medium text-gray-800">{content}</p>
        </div>
      </div>
    </Popup>
  );
}
