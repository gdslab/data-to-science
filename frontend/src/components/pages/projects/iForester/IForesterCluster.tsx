import { FeatureCollection, Point } from 'geojson';
import { useEffect } from 'react';
import { GeoJSONSource, Layer, Source, useMap } from 'react-map-gl/maplibre';
import bboxPolygon from '@turf/bbox-polygon';
import booleanContains from '@turf/boolean-contains';
import { point } from '@turf/helpers';

import {
  clusterLayerInner,
  clusterLayerOuter,
  clusterCountLayer,
  unclusteredPointLayer,
} from './layerProps';

type IForesterClusterProps = { geojsonData: FeatureCollection };

export default function IForesterCluster({
  geojsonData,
}: IForesterClusterProps) {
  const { current: map } = useMap();

  // Update visible markers when map moves
  useEffect(() => {
    if (!map) return;

    const bounds = map.getBounds();
    const mapExtentPolygon = bboxPolygon([
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth(),
    ]);

    let visibleMarkers: string[] = [];
    geojsonData.features.forEach((feature) => {
      const coords = (feature.geometry as Point).coordinates;
      if (
        booleanContains(mapExtentPolygon, point(coords)) &&
        feature.properties?.id
      ) {
        visibleMarkers.push(feature.properties.id);
      }
    });
  });

  // Zoom and click events for cluster layers
  useEffect(() => {
    if (!map) return;

    // Zoom to extent of clicked on cluster symbol
    const handleClick = async (e) => {
      const features = map.queryRenderedFeatures(e.point, {
        layers: ['clusters-inner'],
      });
      const clusterId = features[0].properties.cluster_id;
      const source = map.getSource('iforester-source') as GeoJSONSource;
      const zoom = await source.getClusterExpansionZoom(clusterId);
      const coordinates = (features[0].geometry as Point).coordinates;
      map.easeTo({
        center: [coordinates[0], coordinates[1]],
        zoom,
      });
    };

    // Display pointer style cursor when mouse enters cluster symbol
    const showCursorPointer = () => (map.getCanvas().style.cursor = 'pointer');

    // Remove pointer style cursor when mouse leaves cluster symbol
    const hideCursorPointer = () => (map.getCanvas().style.cursor = '');

    // Cluster events
    map.on('click', 'clusters-inner', handleClick);
    map.on('click', 'clusters-outer', handleClick);
    map.on('mouseenter', 'clusters-inner', showCursorPointer);
    map.on('mouseenter', 'clusters-outer', showCursorPointer);
    map.on('mouseleave', 'clusters-inner', hideCursorPointer);
    map.on('mouseleave', 'clusters-outer', hideCursorPointer);
  }, [map]);

  return (
    <Source
      id="iforester-source"
      type="geojson"
      data={geojsonData}
      cluster={true}
      clusterMaxZoom={14}
      clusterRadius={50}
    >
      <Layer {...clusterLayerOuter} />
      <Layer {...clusterLayerInner} />
      <Layer {...clusterCountLayer} />
      <Layer {...unclusteredPointLayer} />
    </Source>
  );
}
