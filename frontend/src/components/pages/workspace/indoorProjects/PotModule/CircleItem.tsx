import chroma from 'chroma-js';
import clsx from 'clsx';
import { Link } from 'react-router-dom';

import { CircleItemProps } from '../IndoorProject';
import { useShapeContext } from './ShapeContext';

export default function CircleItem({
  group,
  treatment,
  hsvColor,
  url,
}: CircleItemProps) {
  const { shapes } = useShapeContext();
  const { hue, saturation, intensity } = hsvColor;
  const color = chroma.hsv(hue, saturation, intensity).hex();
  const isSaturated = treatment.toLowerCase() === 'saturated';
  const selectedShape = shapes[treatment];

  const shapeClasses = {
    circle: 'rounded-full',
    'rounded-square': 'rounded-lg',
    hexagon: 'clip-hexagon',
    diamond: 'rotate-45',
  };

  return (
    <Link to={url}>
      <div className="flex items-center w-24 h-24">
        <div
          className={clsx(
            'w-full h-full flex items-center justify-center shadow-md',
            shapeClasses[selectedShape],
            {
              'text-white': isSaturated,
              'text-black': !isSaturated,
              'scale-75': selectedShape === 'diamond',
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
          <span className={selectedShape === 'diamond' ? '-rotate-45' : ''}>
            {group.group}
          </span>
        </div>
      </div>
    </Link>
  );
}
