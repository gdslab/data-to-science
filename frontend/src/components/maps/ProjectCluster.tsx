import { AxiosResponse, isAxiosError } from 'axios';
import { Point } from 'geojson';
import { useEffect, useMemo, useState } from 'react';
import { GeoJSONSource, Layer, Source, useMap } from 'react-map-gl/maplibre';

import {
  ProjectFeatureCollection,
  ProjectPointFeature,
} from '../pages/workspace/projects/Project';

import {
  clusterLayerInner,
  clusterLayerOuter,
  clusterCountLayer,
  unclusteredPointLayer,
} from './layerProps';
import { useMapContext } from './MapContext';

import api from '../../api';
import { calculateBoundsFromGeoJSON } from './utils';

type ProjectClusterProps = {
  isMapReady?: boolean;
  fetchFromAPI?: boolean;
  includeAll?: boolean;
  setIsMapReady?: React.Dispatch<React.SetStateAction<boolean>>;
};

export default function ProjectCluster({
  isMapReady,
  fetchFromAPI = false,
  includeAll = false,
  setIsMapReady,
}: ProjectClusterProps) {
  const { projects, projectsLoaded } = useMapContext();

  const [geojsonData, setGeojsonData] =
    useState<ProjectFeatureCollection | null>(null);
  const [geojsonLoaded, setGeojsonLoaded] = useState(false);

  const { current: map } = useMap();

  const projectsFeatureCollection = useMemo(() => {
    if (!projects || projects.length === 0) return null;
    const features: ProjectPointFeature[] = projects.map((project) => ({
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [project.centroid.x, project.centroid.y],
      },
      properties: {
        id: project.id,
        title: project.title,
        description: project.description,
      },
    }));
    const featureCollection: ProjectFeatureCollection = {
      type: 'FeatureCollection',
      features: features,
    };
    return featureCollection;
  }, [projects]);

  // Use context to set project markers if fetchFromAPI is false
  useEffect(() => {
    if (!fetchFromAPI && projects) {
      setGeojsonData(projectsFeatureCollection);
      setGeojsonLoaded(true);
    }
  }, [projectsLoaded]);

  // Fetch project markers in geojson format from api when fetchFromAPI is true
  useEffect(() => {
    const fetchGeojson = async () => {
      try {
        const geojsonUrl = `/projects?include_all=${includeAll}&format=geojson`;
        const response: AxiosResponse<ProjectFeatureCollection> = await api.get(
          geojsonUrl
        );
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

    // Determine animation duration based on whether it's the first load
    const duration = isMapReady === undefined || isMapReady ? 1000 : 1;

    // Set cluster layers as ready after first fitBounds event finishes
    const onMoveEnd = () => {
      if (setIsMapReady) {
        setIsMapReady(true);
      }
    };
    map.once('moveend', onMoveEnd);

    // Fit the map to the bounds
    map.fitBounds(bounds, {
      padding: 20,
      duration: duration,
      maxZoom: 16,
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
