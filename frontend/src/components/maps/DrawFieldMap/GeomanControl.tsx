import * as L from 'leaflet';
import { useFormikContext } from 'formik';
import { useEffect } from 'react';
import { useLeafletContext } from '@react-leaflet/core';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

import { LocationAction } from '../../pages/workspace/projects/ProjectContext/actions';
import { useProjectContext } from '../../pages/workspace/projects/ProjectContext';

interface GeomanOptions extends L.ControlOptions {
  position: L.ControlPosition;
}

export function updateLocation(
  layer: L.Polygon,
  locationDispatch: React.Dispatch<LocationAction>,
  setFieldTouched,
  setFieldValue
): void {
  let layerGeoJSON = layer.toGeoJSON();
  const layerCenter = layer.getCenter();
  layerGeoJSON.properties = {
    center_x: layerCenter.lng,
    center_y: layerCenter.lat,
  };
  locationDispatch({
    type: 'set',
    payload: layerGeoJSON,
  });
  setFieldTouched('location', true);
  setFieldValue('location', layerGeoJSON);
}

export default function GeomanControl({
  isUpdate = false,
  options,
  setGeomanLayer = null,
  layerRef,
  disableDraw = false,
  disableEdit = false,
}: {
  isUpdate?: boolean;
  options: GeomanOptions;
  setGeomanLayer?: React.Dispatch<React.SetStateAction<L.Polygon<any> | null>> | null;
  layerRef;
  disableDraw?: boolean;
  disableEdit?: boolean;
}) {
  const context = useLeafletContext();
  const { setFieldTouched, setFieldValue } = useFormikContext();

  const { location, locationDispatch } = useProjectContext();

  useEffect(() => {
    if (layerRef.current) {
      context.map.fitBounds(layerRef.current.getBounds());
      if (!isUpdate) {
        layerRef.current.on('pm:edit', ({ layer }) => {
          updateLocation(layer, locationDispatch, setFieldTouched, setFieldValue);
        });
      }
    }
  }, [layerRef.current]);

  useEffect(() => {
    context.map.pm.addControls({
      ...options,
      drawPolygon: location || disableDraw ? false : true,
      removalMode: true,
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
      updateLocation(layer, locationDispatch, setFieldTouched, setFieldValue);

      layer.on('pm:edit', ({ layer }: { layer: L.Polygon }) => {
        if (setGeomanLayer) setGeomanLayer(layer);
        updateLocation(layer, locationDispatch, setFieldTouched, setFieldValue);
      });
    });

    context.map.on('pm:globaleditmodetoggled', (e) => {
      if (isUpdate && !e.enabled && e.map.pm.getGeomanLayers().length > 0) {
        const layer = e.map.pm.getGeomanLayers()[0];
        if (layer instanceof L.Polygon) {
          updateLocation(layer, locationDispatch, setFieldTouched, setFieldValue);
        }
      }
    });

    context.map.on('pm:remove', () => {
      setFieldValue('location', {
        center_x: 0,
        center_y: 0,
        geom: '',
      });
      setFieldTouched('location', true);
      locationDispatch({ type: 'clear', payload: null });
      if (setGeomanLayer) setGeomanLayer(null);
    });
  }, []);

  return null;
}
