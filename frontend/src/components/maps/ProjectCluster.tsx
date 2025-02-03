import axios, { AxiosResponse, isAxiosError } from 'axios';
import { FeatureCollection, Point } from 'geojson';
import { useEffect, useState } from 'react';
import { GeoJSONSource, Layer, Source, useMap } from 'react-map-gl/maplibre';

import { useMapContext } from './MapContext';

import {
  clusterLayerInner,
  clusterLayerOuter,
  clusterCountLayer,
  unclusteredPointLayer,
} from './layerProps';

import { calculateBoundsFromGeoJSON } from './utils';

type ProjectClusterProps = { fetchFromAPI?: boolean; includeAll?: boolean };

export default function ProjectCluster({
  fetchFromAPI = false,
  includeAll = false,
}: ProjectClusterProps) {
  const { projectGeojson, projectGeojsonLoaded } = useMapContext();

  const [geojsonData, setGeojsonData] =
    useState<FeatureCollection<Point> | null>(null);
  const [geojsonLoaded, setGeojsonLoaded] = useState(false);

  const { current: map } = useMap();

  // Use context to set project markers if fetchFromAPI is false
  useEffect(() => {
    if (!fetchFromAPI) {
      setGeojsonData(projectGeojson);
      setGeojsonLoaded(true);
    }
  }, [projectGeojsonLoaded]);

  // Fetch project markers in geojson format from api when fetchFromAPI is true
  useEffect(() => {
    const fetchGeojson = async () => {
      try {
        const geojsonUrl = `${
          import.meta.env.VITE_API_V1_STR
        }/projects?include_all=${includeAll}&format=geojson`;
        const response: AxiosResponse<FeatureCollection<Point>> =
          await axios.get(geojsonUrl);
        setGeojsonData(response.data);
        setGeojsonLoaded(true);
      } catch (error) {
        if (isAxiosError(error)) {
          // Axios-specific error handling
          const status = error.response?.status || 500;
          const message = error.response?.data?.message || error.message;

          throw {
            status,
            message: `Failed to load project geojson: ${message}`,
          };
        } else {
          // Generic error handling
          throw {
            status: 500,
            message: 'An unexpected error occurred.',
          };
        }
      }
    };

    if (fetchFromAPI) {
      fetchGeojson();
    }
  }, []);

  // Zoom to extent of project markers
  useEffect(() => {
    if (!map || !geojsonLoaded || !geojsonData) return;

    // Fetch project GeoJSON data to calculate the bounds
    const bounds = calculateBoundsFromGeoJSON(geojsonData);

    // Fit the map to the bounds
    map.fitBounds(bounds, {
      padding: 20,
      duration: 1000,
    });
  }, [map, geojsonData, geojsonLoaded]);

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

  if (!geojsonLoaded || !geojsonData) return null;

  return (
    <Source
      id="projects"
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
