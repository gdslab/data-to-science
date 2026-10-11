import chroma from 'chroma-js';
import clsx from 'clsx';
import { Link } from 'react-router';

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
  const selectedShape = shapes[treatment];
  const isFilled = selectedShape.endsWith('-filled');

  const baseShapeClasses = {
    circle: 'rounded-full',
    'rounded-square': 'rounded-lg',
    diamond: 'rotate-45',
  } as const;

  return (
    <Link to={url}>
      <div className="flex items-center w-24 h-24">
        <div
          className={clsx(
            'w-full h-full flex items-center justify-center shadow-md',
            baseShapeClasses[
              selectedShape.replace('-filled', '') as
                | 'circle'
                | 'rounded-square'
                | 'diamond'
            ],
            {
              'text-white': isFilled,
              'text-black': !isFilled,
              'scale-75': selectedShape.startsWith('diamond'),
            }
          )}
          style={{
            backgroundColor: isFilled ? color : 'transparent',
            border: isFilled ? 'none' : `8px solid ${color}`,
          }}
          title={`H: ${hue?.toFixed(2)}, S: ${saturation?.toFixed(
            2
          )}, V: ${intensity?.toFixed(2)}`}
        >
          <span
            className={
              selectedShape === 'diamond' || selectedShape === 'diamond-filled'
                ? '-rotate-45'
                : ''
            }
          >
            {group.group}
          </span>
        </div>
      </div>
    </Link>
  );
}
