import { useState } from 'react';
import {
  ChevronDoubleDownIcon,
  ChevronDoubleUpIcon,
} from '@heroicons/react/24/outline';

import { useMapLayerContext } from './MapLayersContext';
import OpacitySlider from './OpacitySlider';

export default function MaplibreLayerControl() {
  const [visible, setVisible] = useState(true);

  const {
    state: { layers },
    dispatch,
  } = useMapLayerContext();

  const updateLayerProperty = (
    layerId: string,
    property: 'checked' | 'color' | 'opacity',
    value: boolean | number | string
  ) => {
    const updatedLayers = layers.map((layer) =>
      layer.id === layerId ? { ...layer, [property]: value } : layer
    );
    dispatch({ type: 'SET_LAYERS', payload: updatedLayers });
  };

  const toggleVisibility = () => setVisible(!visible);

  return (
    <div className="absolute top-0 left-0 max-w-80 bg-white shadow-md px-3 py-6 m-5 leading-3 text-slate-600 outline-none">
      <h3>Map Layers</h3>
      <p className="text-sm text-slate-500 italic">
        Toggle map layer on/off, change layer color, and adjust layer opacity.
      </p>
      <hr className="my-2" />
      {visible && (
        <div className="flex flex-col gap-4">
          {layers.map((layer) => (
            <div key={layer.id} className="flex flex-col gap-2.5">
              <div className="flex items-center justify-between text-sm gap-2">
                <label className="inline-block w-40 truncate">{layer.name}</label>
                <div className="flex items-center">
                  <input
                    className="ml-5"
                    type="checkbox"
                    checked={layer.checked}
                    onChange={(event) =>
                      updateLayerProperty(layer.id, 'checked', event.target.checked)
                    }
                  />
                  <input
                    className="ml-5 h-6 w-12 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    type="color"
                    value={layer.color}
                    disabled={!layer.checked}
                    onChange={(event) =>
                      updateLayerProperty(layer.id, 'color', event.target.value)
                    }
                  />
                </div>
              </div>
              <div className="pr-2">
                <OpacitySlider
                  disabled={!layer.checked}
                  currentValue={layer.opacity}
                  onChange={(_, newValue: number | number[]) => {
                    if (typeof newValue === 'number') {
                      updateLayerProperty(layer.id, 'opacity', newValue);
                    }
                  }}
                />
              </div>
            </div>
          ))}
          {layers.length === 0 && (
            <span className="text-sm">
              No map layers found for this project. Add map layers from the project
              page.
            </span>
          )}
        </div>
      )}
      <div className="relative flex justify-center p-1.5">
        <button
          type="button"
          className="absolute focus:outline-none hover:bg-gray-100 focus:ring focus:ring-accent2"
          aria-label={visible ? 'Hide map layers' : 'Show map layers'}
          aria-expanded={visible}
          onClick={toggleVisibility}
        >
          {visible ? (
            <ChevronDoubleUpIcon className="h-6 w-6" />
          ) : (
            <ChevronDoubleDownIcon className="h-6 w-6" />
          )}
          <span className="sr-only">
            {visible ? 'Hide map layers' : 'Show map layers'}
          </span>
        </button>
      </div>
    </div>
  );
}
