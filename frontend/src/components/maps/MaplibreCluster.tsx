import axios, { AxiosResponse } from 'axios';
import { FeatureCollection, Point } from 'geojson';
import { useEffect } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';

import {
  clusterLayer,
  clusterCountLayer,
  unclusteredPointLayer,
} from './MaplibreClusterLayers';

export default function MaplibreCluster() {
  const { current: map } = useMap();
  const geojsonUrl = `${import.meta.env.VITE_API_V1_STR}/projects?format=geojson`;

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
        const bounds: [number, number, number, number] = geojsonData.features.reduce(
          (bounds, feature) => {
            const [minLng, minLat, maxLng, maxLat] = bounds;
            const [lng, lat] = feature.geometry.coordinates;
            return [
              Math.min(minLng, lng),
              Math.min(minLat, lat),
              Math.max(maxLng, lng),
              Math.max(maxLat, lat),
            ];
          },
          [Infinity, Infinity, -Infinity, -Infinity]
        );

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
      <Layer {...clusterLayer} />
      <Layer {...clusterCountLayer} />
      <Layer {...unclusteredPointLayer} />
    </Source>
  );
}
