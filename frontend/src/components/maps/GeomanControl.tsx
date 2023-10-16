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
  setGeomanLayer = null,
  layerRef,
  disableDraw = false,
  disableEdit = false,
  disableRemove = false,
}: {
  options: GeomanOptions;
  location: Location | null;
  setLocation: SetLocation;
  setGeomanLayer?: React.Dispatch<React.SetStateAction<L.Polygon<any> | null>> | null;
  layerRef;
  disableDraw?: boolean;
  disableEdit?: boolean;
  disableRemove?: boolean;
}) {
  const context = useLeafletContext();

  useEffect(() => {
    if (layerRef.current) {
      context.map.fitBounds(layerRef.current.getBounds());
      layerRef.current.on('pm:edit', ({ layer }) => {
        setLocation({
          geojson: layer.toGeoJSON(),
          center: layer.getCenter(),
          type: location ? location.type : 'drawn',
        });
      });
    }
  }, []);

  useEffect(() => {
    context.map.pm.addControls({
      ...options,
      drawPolygon: location || disableDraw ? false : true,
      removalMode: !disableRemove,
      drawMarker: false,
      drawCircle: false,
      drawCircleMarker: false,
      drawPolyline: false,
      drawRectangle: false,
      drawText: false,
      editMode: !disableEdit,
      dragMode: false,
      rotateMode: false,
      cutPolygon: false,
    });

    context.map.on('pm:create', ({ layer }: { layer: L.Polygon }) => {
      if (setGeomanLayer) setGeomanLayer(layer);
      setLocation({
        geojson: layer.toGeoJSON(),
        center: layer.getCenter(),
        type: 'drawn',
      });
    });
    context.map.on('pm:remove', () => {
      setLocation(null);
    });
  }, []);

  return null;
}
