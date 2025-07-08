import { Menu } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import './shapes.css';
import { useShapeContext, Shape } from './ShapeContext';

const shapes: { value: Shape; label: string }[] = [
  { value: 'circle', label: 'Circle' },
  { value: 'rounded-square', label: 'Rounded Square' },
  { value: 'hexagon', label: 'Hexagon' },
  { value: 'diamond', label: 'Diamond' },
];

const shapeClasses = {
  circle: 'rounded-full',
  'rounded-square': 'rounded-lg',
  hexagon: 'clip-hexagon',
  diamond: 'rotate-45',
};

function ShapeSelector({ treatment }: { treatment: string }) {
  const { shapes: selectedShapes, setShape } = useShapeContext();
  const selectedShape = selectedShapes[treatment];

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="flex items-center gap-4 hover:bg-gray-100 p-2 rounded-lg">
        <div
          className={`h-12 w-12 ${shapeClasses[selectedShape]} ${
            treatment.toLowerCase() === 'saturated'
              ? 'bg-black'
              : 'border-8 border-black'
          }`}
        />
        <span className="capitalize">{treatment}</span>
        <ChevronDownIcon className="h-5 w-5" />
      </Menu.Button>
      <Menu.Items className="absolute z-10 mt-2 w-56 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
        <div className="py-1">
          {shapes.map((shape) => (
            <Menu.Item key={shape.value}>
              {({ active }) => (
                <button
                  onClick={() => setShape(treatment, shape.value)}
                  className={`${
                    active ? 'bg-gray-100' : ''
                  } flex items-center gap-4 w-full px-4 py-2 text-left`}
                >
                  <div
                    className={`h-8 w-8 ${shapeClasses[shape.value]} ${
                      treatment.toLowerCase() === 'saturated'
                        ? 'bg-black'
                        : 'border-4 border-black'
                    }`}
                  />
                  <span>{shape.label}</span>
                </button>
              )}
            </Menu.Item>
          ))}
        </div>
      </Menu.Items>
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
