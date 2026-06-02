import { useEffect, useRef } from 'react';

import { MapLayerProps } from '../MapLayersContext';
import { sorter } from '../../utils';

export type MapLayerSortSelection = 'atoz' | 'ztoa';

const STORAGE_KEY = 'mapLayerSortPreference';

const categories = [
  { key: 'atoz', label: 'Name A-Z', title: 'Sort by layer name ascending' },
  { key: 'ztoa', label: 'Name Z-A', title: 'Sort by layer name descending' },
];

export function sortMapLayers(
  layers: MapLayerProps[],
  selection: MapLayerSortSelection
): MapLayerProps[] {
  return [...layers].sort((a, b) => {
    if (selection === 'ztoa') {
      return sorter(a.name.toLowerCase(), b.name.toLowerCase(), 'desc');
    }
    return sorter(a.name.toLowerCase(), b.name.toLowerCase());
  });
}

export function getMapLayerSortPreference(): MapLayerSortSelection {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'atoz' || stored === 'ztoa') {
    return stored;
  }
  return 'atoz';
}

function setMapLayerSortPreference(value: MapLayerSortSelection) {
  localStorage.setItem(STORAGE_KEY, value);
}

function getSortOptionLabel(selection: MapLayerSortSelection): string {
  return categories.find(({ key }) => key === selection)?.label ?? 'Unknown';
}

export default function MapLayerSort({
  sortSelection,
  setSortSelection,
  isOpen,
  onOpen,
  onClose,
}: {
  sortSelection: MapLayerSortSelection;
  setSortSelection: React.Dispatch<React.SetStateAction<MapLayerSortSelection>>;
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
}) {
  const detailsRef = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (detailsRef.current?.open && event.target) {
        if (!detailsRef.current.contains(event.target as HTMLElement)) {
          detailsRef.current.removeAttribute('open');
          onClose();
        }
      }
    };
    window.addEventListener('click', handleClickOutside);
    return () => {
      window.removeEventListener('click', handleClickOutside);
    };
  }, [onClose]);

  function onChange(event: React.ChangeEvent<HTMLInputElement>) {
    if (event.target.checked) {
      const value = event.target.value as MapLayerSortSelection;
      setSortSelection(value);
      setMapLayerSortPreference(value);
    }
  }

  return (
    <div className="flex gap-8">
      <div className="relative">
        <details
          ref={detailsRef}
          className="group [&_summary::-webkit-details-marker]:hidden"
          open={isOpen}
          onToggle={(e) => {
            if (e.currentTarget.open) {
              onOpen();
            } else {
              onClose();
            }
          }}
        >
          <summary className="flex cursor-pointer items-center gap-2 border-b border-gray-400 pb-1 text-gray-900 transition hover:border-gray-600">
            <span className="w-36 text-sm font-medium">
              Sort by: {getSortOptionLabel(sortSelection)}
            </span>
            <span className="transition group-open:-rotate-180">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                className="h-4 w-4"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                />
              </svg>
            </span>
          </summary>

          <div className="z-50 group-open:absolute group-open:start-0 group-open:top-auto group-open:mt-2">
            <div className="rounded-sm border border-gray-200 bg-white">
              <ul className="space-y-1 border-t border-gray-200 p-4">
                {categories.map(({ key, label, title }) => (
                  <li key={key}>
                    <label
                      htmlFor={`layer-sort-${key}`}
                      className="inline-flex items-center gap-2"
                      title={title}
                    >
                      <input
                        type="radio"
                        name="layerSortOption"
                        id={`layer-sort-${key}`}
                        className="size-5 text-accent2 border-gray-300"
                        value={key}
                        checked={sortSelection === key}
                        onChange={onChange}
                      />
                      <span className="text-sm font-medium text-gray-700">
                        {label}
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </details>
      </div>
    </div>
  );
}
