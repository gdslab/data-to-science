import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import './shapes.css';
import { useShapeContext, Shape } from './ShapeContext';

const shapes: { value: Shape; label: string }[] = [
  { value: 'circle', label: 'Circle (Hollow)' },
  { value: 'circle-filled', label: 'Circle (Filled)' },
  { value: 'rounded-square', label: 'Rounded Square (Hollow)' },
  { value: 'rounded-square-filled', label: 'Rounded Square (Filled)' },
  { value: 'diamond', label: 'Diamond (Hollow)' },
  { value: 'diamond-filled', label: 'Diamond (Filled)' },
];

const baseShapeClasses: Record<Exclude<Shape, `${string}-filled`>, string> = {
  circle: 'rounded-full',
  'rounded-square': 'rounded-lg',
  diamond: 'rotate-45',
};

function getShapeClass(shape: Shape, borderClass: string): string {
  const isFilled = shape.endsWith('-filled');
  const base = shape.replace('-filled', '') as Exclude<
    Shape,
    `${string}-filled`
  >;
  const fillOrBorder = isFilled ? 'bg-black' : `${borderClass} border-black`;
  const scaleForDiamond = base === 'diamond' ? 'scale-90' : '';
  return `${baseShapeClasses[base]} ${fillOrBorder} ${scaleForDiamond}`.trim();
}

function ShapeSelector({ treatment }: { treatment: string }) {
  const { shapes: selectedShapes, setShape } = useShapeContext();
  const selectedShape = selectedShapes[treatment];

  return (
    <Menu as="div" className="relative">
      <MenuButton className="flex items-center gap-4 hover:bg-gray-100 p-2 rounded-lg min-w-0">
        <div
          className={`inline-flex items-center justify-center h-10 w-10 ${getShapeClass(
            selectedShape,
            'border-4'
          )}`}
        />
        <span className="capitalize truncate flex-1 min-w-0">{treatment}</span>
        <ChevronDownIcon className="h-5 w-5" />
      </MenuButton>
      <MenuItems className="absolute z-10 mt-2 w-56 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
        <div className="py-1">
          {shapes.map((shape) => (
            <MenuItem key={shape.value}>
              {({ active }) => (
                <button
                  onClick={() => setShape(treatment, shape.value)}
                  className={`${
                    active ? 'bg-gray-100' : ''
                  } flex items-center gap-4 w-full px-4 py-2 text-left`}
                >
                  <div
                    className={`inline-flex items-center justify-center h-6 w-6 ${getShapeClass(
                      shape.value,
                      'border-2'
                    )}`}
                  />
                  <span>{shape.label}</span>
                </button>
              )}
            </MenuItem>
          ))}
        </div>
      </MenuItems>
    </Menu>
  );
}

export default function Legend({ treatments }: { treatments: string[] }) {
  return (
    <div className="flex flex-col gap-2">
      {treatments.map((treatment) => (
        <ShapeSelector key={treatment} treatment={treatment} />
      ))}
    </div>
  );
}
