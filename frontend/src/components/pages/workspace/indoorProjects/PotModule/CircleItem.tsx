import chroma from 'chroma-js';
import clsx from 'clsx';
import { Link } from 'react-router-dom';

import { CircleItemProps } from '../IndoorProject';

export default function CircleItem({
  group,
  treatment,
  hsvColor,
  url,
}: CircleItemProps) {
  const { hue, saturation, intensity } = hsvColor;
  const color = chroma.hsv(hue, saturation / 100, intensity / 100).hex();
  const isSaturated = treatment.toLowerCase() === 'saturated';

  return (
    <Link to={url}>
      <div className="flex items-center w-24 h-24">
        <div
          className={clsx(
            'w-full h-full rounded-full flex items-center justify-center shadow-md',
            {
              'text-white': isSaturated,
              'text-black': !isSaturated,
            }
          )}
          style={{
            backgroundColor: isSaturated ? color : 'none',
            border: `8px solid ${color}`,
          }}
          title={`H: ${hue?.toFixed(2)}, S: ${saturation?.toFixed(
            2
          )}, V: ${intensity?.toFixed(2)}`}
        >
          {group.group}
        </div>
      </div>
    </Link>
  );
}
