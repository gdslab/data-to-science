import axios, { AxiosResponse } from 'axios';
import { FeatureCollection, Point } from 'geojson';
import { useEffect } from 'react';
import { GeoJSONSource, Layer, Source, useMap } from 'react-map-gl/maplibre';

import {
  clusterLayerInner,
  clusterLayerOuter,
  clusterCountLayer,
  unclusteredPointLayer,
} from './MaplibreLayers';

import { calculateBoundsFromGeoJSON } from './utils';

export default function MaplibreCluster() {
  const { current: map } = useMap();
  const geojsonUrl = `${import.meta.env.VITE_API_V1_STR}/projects?format=geojson`;

  useEffect(() => {
    if (!map) return;

    // Zoom to extent of clicked on cluster symbol
    const handleClick = async (e) => {
      const features = map.queryRenderedFeatures(e.point, {
        layers: ['clusters-inner'],
      });
      const clusterId = features[0].properties.cluster_id;
      const source = map.getSource('projects') as GeoJSONSource;
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

  useEffect(() => {
    if (!map) return;

    // Fetch project GeoJSON data to calculate the bounds
    const fetchGeoJSONAndFitBounds = async () => {
      try {
        const response: AxiosResponse<FeatureCollection<Point>> = await axios.get(
          geojsonUrl
        );
        const geojsonData = await response.data;

        // Calculate the bounds of the GeoJSON features
        const bounds = calculateBoundsFromGeoJSON(geojsonData);

        // Fit the map to the bounds
        map.fitBounds(bounds, {
          padding: 20,
          duration: 1000,
        });
      } catch (error) {
        console.error('Error fetching or processing project GeoJSON data:', error);
      }
    };

    fetchGeoJSONAndFitBounds();
  }, [map, geojsonUrl]);

  return (
    <Source
      id="projects"
      type="geojson"
      data={geojsonUrl}
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
