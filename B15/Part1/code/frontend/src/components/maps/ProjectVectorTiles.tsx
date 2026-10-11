import { useEffect, useRef } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';

import { getProjectVectorLayer } from './layerProps';
import { useMapLayerContext } from './MapLayersContext';

export default function ProjectVectorTile() {
  const {
    state: { layers },
  } = useMapLayerContext();
  const { current: map } = useMap();
  const previousLayersRef = useRef<Set<string>>(new Set());

  // Clean up layers that were unchecked (polygon layers create border layers)
  useEffect(() => {
    if (!map) return;

    const mapInstance = map.getMap();

    const currentLayerIds = new Set(
      layers.filter((layer) => layer.checked).map((layer) => layer.id)
    );

    // Find layers that were removed (previously checked, now unchecked)
    const removedLayerIds = Array.from(previousLayersRef.current).filter(
      (id) => !currentLayerIds.has(id)
    );

    // Clean up removed layers
    removedLayerIds.forEach((layerId) => {
      // Remove border layer first (for polygon layers)
      const borderLayerId = `${layerId}-border`;
      if (mapInstance.getLayer(borderLayerId)) {
        mapInstance.removeLayer(borderLayerId);
      }

      // Remove main layer
      if (mapInstance.getLayer(layerId)) {
        mapInstance.removeLayer(layerId);
      }

      // Remove source last
      if (mapInstance.getSource(layerId)) {
        mapInstance.removeSource(layerId);
      }
    });

    previousLayersRef.current = currentLayerIds;
  }, [layers, map]);

  return layers
    .filter((layer) => layer.checked)
    .map((layer) => {
      const vectorLayer = getProjectVectorLayer(layer);
      const renderLayer = (props) => <Layer key={props.id} {...props} />;

      return (
        <Source
          key={layer.id}
          id={layer.id}
          type="vector"
          tiles={[layer.signedUrl]}
          minzoom={12}
          maxzoom={24}
        >
          {
            Array.isArray(vectorLayer)
              ? vectorLayer.map(renderLayer) // Render multiple layers if vectorLayer is an array
              : renderLayer(vectorLayer) // Render a single layer otherwise
          }
        </Source>
      );
    });
}
