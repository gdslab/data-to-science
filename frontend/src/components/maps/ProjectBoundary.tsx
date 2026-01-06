import { AxiosResponse } from 'axios';
import { FeatureCollection, Polygon } from 'geojson';
import { useEffect, useRef, useState } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';
import bbox from '@turf/bbox';
import center from '@turf/center';

import { projectBoundaryLayer } from './layerProps';
import { BBox } from './Maps';
import { useMapContext } from './MapContext';

import api from '../../api';

type ProjectBoundaryProps = {
  setActiveProjectBBox?: React.Dispatch<React.SetStateAction<BBox | null>>;
  setViewState?: React.Dispatch<
    React.SetStateAction<{
      longitude: number;
      latitude: number;
      zoom: number;
    }>
  >;
};

export default function ProjectBoundary({
  setActiveProjectBBox,
  setViewState,
}: ProjectBoundaryProps) {
  const [projectBoundary, setProjectBoundary] =
    useState<FeatureCollection<Polygon> | null>(null);
  const { current: map } = useMap();
  const {
    activeMapTool,
    activeProject,
    mapViewProperties,
    mapViewPropertiesDispatch,
  } = useMapContext();
  const geojsonUrl = `/projects/${activeProject?.id}?format=geojson`;

  // Store zoom in ref to access latest value without triggering effect
  const zoomRef = useRef(mapViewProperties?.zoom ?? 12);

  // Update ref when mapViewProperties changes (doesn't trigger re-render)
  useEffect(() => {
    if (mapViewProperties?.zoom !== undefined) {
      zoomRef.current = mapViewProperties.zoom;
    }
  }, [mapViewProperties?.zoom]);

  useEffect(() => {
    if (!map) return;
    // Fetch project boundary GeoJSON to calculate the bounds
    const fetchGeoJSONAndFitBounds = async () => {
      try {
        const response: AxiosResponse<FeatureCollection<Polygon>> =
          await api.get(geojsonUrl);
        const geojsonData = await response.data;
        setProjectBoundary(geojsonData);
        // Calculate the bounds of the GeoJSON feature
        const bounds = bbox(geojsonData) as BBox;
        if (setActiveProjectBBox) {
          setActiveProjectBBox(bounds);
        }

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
            zoom: zoomRef.current,
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
  }, [
    activeMapTool,
    geojsonUrl,
    map,
    mapViewPropertiesDispatch,
    setActiveProjectBBox,
    setViewState,
  ]);

  if (!projectBoundary) return null;

  return (
    <Source id="project-boundary" type="geojson" data={projectBoundary}>
      <Layer {...projectBoundaryLayer} />
    </Source>
  );
}
