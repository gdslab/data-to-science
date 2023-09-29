import * as L from 'leaflet';
import { useEffect } from 'react';
import { useLeafletContext } from '@react-leaflet/core';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

import { Location, SetLocation } from '../pages/projects/ProjectForm';

interface GeomanOptions extends L.ControlOptions {
  position: L.ControlPosition;
}

export default function GeomanControl({
  options,
  location,
  setLocation,
}: {
  options: GeomanOptions;
  location: Location | null;
  setLocation: SetLocation;
}) {
  const context = useLeafletContext();

  useEffect(() => {
    context.map.pm.addControls({
      ...options,
      drawPolygon: location ? false : true,
      removalMode: true,
      drawMarker: false,
      drawCircle: false,
      drawCircleMarker: false,
      drawPolyline: false,
      drawRectangle: false,
      drawText: false,
      editMode: location ? true : false,
      dragMode: false,
      rotateMode: false,
      cutPolygon: false,
    });

    context.map.on('pm:create', ({ layer }: { layer: L.Polygon }) => {
      setLocation({
        geojson: layer.toGeoJSON(),
        center: layer.getCenter(),
      });
    });
  });

  return null;
}
