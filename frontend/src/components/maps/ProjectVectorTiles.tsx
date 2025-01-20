import { Layer, Source } from 'react-map-gl/maplibre';

import { getProjectVectorLayer } from './layerProps';
import { useMapLayerContext } from './MapLayersContext';

export default function ProjectVectorTile() {
  const {
    state: { layers },
  } = useMapLayerContext();

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
