import axios, { AxiosResponse } from 'axios';
import { FeatureCollection, Polygon } from 'geojson';
import { useEffect } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';
import center from '@turf/center';

import { projectBoundaryLayer } from './layerProps';
import { useMapContext } from './MapContext';

import { calculateBoundsFromGeoJSON } from './utils';

type ProjectBoundaryProps = {
  setViewState?: React.Dispatch<
    React.SetStateAction<{
      longitude: number;
      latitude: number;
      zoom: number;
    }>
  >;
};

export default function ProjectBoundary({ setViewState }: ProjectBoundaryProps) {
  const { current: map } = useMap();
  const { activeMapTool, activeProject, mapViewProperties, mapViewPropertiesDispatch } =
    useMapContext();
  const geojsonUrl = `${import.meta.env.VITE_API_V1_STR}/projects/${
    activeProject?.id
  }?format=geojson`;

  useEffect(() => {
    if (!map) return;
    // Fetch project boundary GeoJSON to calculate the bounds
    const fetchGeoJSONAndFitBounds = async () => {
      try {
        const response: AxiosResponse<FeatureCollection<Polygon>> = await axios.get(
          geojsonUrl
        );
        const geojsonData = await response.data;

        // Calculate the bounds of the GeoJSON feature
        const bounds: [number, number, number, number] =
          calculateBoundsFromGeoJSON(geojsonData);

        if (!setViewState) {
          // Fit the map to the bounds
          map.fitBounds(bounds, {
            padding: 20,
            duration: 1000,
          });
          setTimeout(() => {
            mapViewPropertiesDispatch({
              type: 'SET_VIEW_PROPERTIES',
              payload: { zoom: map.getZoom() },
            });
          }, 1000);
        } else {
          // Get center lat/lng
          const bboxCenter = center(geojsonData).geometry.coordinates;
          // Set view to center coordinates and zoom level set when project loaded
          setViewState((prev) => ({
            ...prev,
            longitude: bboxCenter[0],
            latitude: bboxCenter[1],
            zoom: mapViewProperties ? mapViewProperties.zoom : 12,
          }));
        }
      } catch (error) {
        console.error(
          'Error fetching or processing project boundary GeoJSON data:',
          error
        );
      }
    };

    fetchGeoJSONAndFitBounds();
  }, [activeMapTool, map, geojsonUrl]);

  return (
    <Source id="project-boundary" type="geojson" data={geojsonUrl}>
      <Layer {...projectBoundaryLayer} />
    </Source>
  );
}
