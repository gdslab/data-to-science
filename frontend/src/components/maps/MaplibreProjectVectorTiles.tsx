import { Layer, Source } from 'react-map-gl/maplibre';

import { getProjectVectorLayer } from './MaplibreLayers';
import { useMapLayerContext } from './MapLayersContext';

function getTilesUrl(layerId: string): string {
  return `${import.meta.env.VITE_BASE_URL}${
    import.meta.env.VITE_API_V1_STR
  }/public/vectortiles?layer_id=${layerId}&x={x}&y={y}&z={z}`;
}

export default function MaplibreProjectVectorTile() {
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
          minzoom={0}
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
