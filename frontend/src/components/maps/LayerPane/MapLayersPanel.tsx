import { useMapLayerContext } from '../MapLayersContext';
import OpacitySlider from '../OpacitySlider';

export default function MapLayersPanel() {
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

  if (layers.length === 0) {
    return (
      <div className="text-sm text-slate-500 italic p-2">
        No map layers found for this project. Add map layers from the project
        page.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {layers.map((layer) => (
        <div key={layer.id} className="flex flex-col p-2 bg-slate-50 rounded">
          {/* Layer name and controls row */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <input
                type="checkbox"
                checked={layer.checked}
                onChange={(event) =>
                  updateLayerProperty(layer.id, 'checked', event.target.checked)
                }
                className="h-4 w-4 shrink-0 text-accent2 focus:ring-accent2"
              />
              <label
                className="text-sm font-medium truncate"
                title={layer.name}
              >
                {layer.name}
              </label>
            </div>
            <input
              type="color"
              value={layer.color}
              disabled={!layer.checked}
              onChange={(event) =>
                updateLayerProperty(layer.id, 'color', event.target.value)
              }
              className="h-7 w-10 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
            />
          </div>

          {/* Opacity slider */}
          <div className="pl-1 pr-4 py-2">
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
    </div>
  );
}
