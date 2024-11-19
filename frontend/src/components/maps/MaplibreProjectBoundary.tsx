import axios, { AxiosResponse } from 'axios';
import { FeatureCollection, Polygon } from 'geojson';
import { useEffect } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';

import { projectBoundaryLayer } from './MaplibreLayers';
import { useMapContext } from './MapContext';

import { calculateBoundsFromGeoJSON } from './utils';

export default function MaplibreProjectBoundary() {
  const { current: map } = useMap();
  const { activeProject } = useMapContext();
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

        // Fit the map to the bounds
        map.fitBounds(bounds, {
          padding: 20,
          duration: 1000,
        });
      } catch (error) {
        console.error(
          'Error fetching or processing project boundary GeoJSON data:',
          error
        );
      }
    };

    fetchGeoJSONAndFitBounds();
  }, [map, geojsonUrl]);

  return (
    <Source id="project-boundary" type="geojson" data={geojsonUrl}>
      <Layer {...projectBoundaryLayer} />
    </Source>
  );
}
