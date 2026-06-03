import { useEffect } from 'react';
import { FeatureCollection, Polygon } from 'geojson';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';

type GridOverlayProps = {
  data: FeatureCollection<Polygon>;
  side: 'left' | 'right';
};

export default function GridOverlay({ data, side }: GridOverlayProps) {
  const sourceId = `compare-grid-${side}`;
  const layerId = `compare-grid-layer-${side}`;
  const { current: map } = useMap();

  // Keep the grid layer on top of raster layers. ProjectRasterTiles re-inserts
  // its raster on top whenever data/symbology changes, so we re-assert our
  // position on every 'idle' event (the guard avoids a move→idle loop).
  useEffect(() => {
    if (!map) return;

    const moveGridToTop = () => {
      if (!map.getLayer(layerId)) return;
      const order = map.getLayersOrder();
      if (order[order.length - 1] !== layerId) {
        map.moveLayer(layerId);
      }
    };

    moveGridToTop();
    map.on('idle', moveGridToTop);

    return () => {
      map.off('idle', moveGridToTop);
    };
  }, [map, layerId]);

  return (
    <Source id={sourceId} type="geojson" data={data}>
      <Layer
        id={layerId}
        type="line"
        source={sourceId}
        paint={{
          'line-color': '#ffffff',
          'line-opacity': 0.4,
          'line-width': 2,
          'line-dasharray': [4, 4],
        }}
      />
    </Source>
  );
}
