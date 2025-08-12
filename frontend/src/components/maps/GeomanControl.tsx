import '@geoman-io/maplibre-geoman-free/dist/maplibre-geoman.css';
import 'maplibre-gl/dist/maplibre-gl.css';

import { useEffect, useRef, useCallback } from 'react';
import { useMap } from 'react-map-gl';
import {
  GeoJsonImportFeature,
  GeoJsonShapeFeature,
  Geoman,
} from '@geoman-io/maplibre-geoman-free';

import { LocationAction } from '../pages/projects/ProjectContext/actions';
import { geomanOptions } from './styles/geomanOptions';
import { GeoJSONFeature } from '../pages/projects/Project';
import { fitMapToGeoJSON } from './utils';

interface GeomanControlProps {
  editFeature?: GeoJSONFeature | null;
  onDrawStart?: () => void;
  onDrawEnd?: (feature: GeoJsonShapeFeature) => void;
  onEdit?: (feature: GeoJsonShapeFeature) => void;
  featureLimit?: number;
  disabled?: boolean;
}

export default function GeomanControl({
  editFeature = null,
  onDrawStart,
  onDrawEnd,
  onEdit,
  featureLimit = 1,
  disabled = false,
}: GeomanControlProps) {
  const { current: map } = useMap();

  const geomanRef = useRef<Geoman | null>(null);
  const drawnFeaturesCount = useRef(0);
  const initializedRef = useRef(false);

  // Memoize event handlers to prevent unnecessary re-renders
  const handleDrawStart = useCallback(
    (_event: any) => {
      // Reset feature count when drawing starts (clean slate)
      drawnFeaturesCount.current = 0;

      // Remove any existing polygons when drawing starts
      if (geomanRef.current) {
        try {
          // Remove all existing features
          geomanRef.current.features.forEach((featureData) => {
            geomanRef.current?.features.delete(featureData.id);
          });
        } catch (error) {
          console.warn('Error removing existing features:', error);
        }
      }

      if (onDrawStart) {
        onDrawStart();
      }
    },
    [onDrawStart]
  );

  const handleDrawEnd = useCallback(
    (event: any) => {
      const feature: GeoJsonShapeFeature = event.feature.getGeoJson();
      drawnFeaturesCount.current += 1;

      if (onDrawEnd) {
        onDrawEnd(feature);
      }

      // Disable drawing mode if feature limit is reached
      if (drawnFeaturesCount.current >= featureLimit && geomanRef.current) {
        geomanRef.current.disableDraw();
      }
    },
    [onDrawEnd, featureLimit]
  );

  const handleEdit = useCallback(
    (event: any) => {
      const feature: GeoJsonShapeFeature = event.feature.getGeoJson();

      if (onEdit) {
        onEdit(feature);
      }
    },
    [onEdit]
  );

  const handleRemove = useCallback(
    (_event: any) => {
      // Reset feature count when polygon is removed
      drawnFeaturesCount.current = 0;

      // Call the same handler as draw start to reset formik field
      if (onDrawStart) {
        onDrawStart();
      }
    },
    [onDrawStart]
  );

  // Initialize Geoman only once
  useEffect(() => {
    if (!map || initializedRef.current) return;

    const mapInstance = map.getMap();

    // Callback to initialize Geoman after map is fully loaded
    const initializeGeoman = () => {
      if (geomanRef.current || initializedRef.current) return;

      try {
        geomanRef.current = new Geoman(mapInstance, geomanOptions);
        initializedRef.current = true;

        // Import existing feature if it exists
        if (editFeature) {
          mapInstance.on('gm:loaded', () => {
            geomanRef.current?.features.importGeoJsonFeature(
              editFeature as GeoJsonImportFeature
            );
            fitMapToGeoJSON(
              mapInstance as unknown as maplibregl.Map,
              editFeature as GeoJsonImportFeature
            );
          });
        }

        // Add event listeners for drawing events
        mapInstance.on('gm:drawstart', handleDrawStart);
        mapInstance.on('gm:create', handleDrawEnd);
        mapInstance.on('gm:editend', handleEdit);
        mapInstance.on('gm:remove', handleRemove);
      } catch (error) {
        console.error('Error initializing Geoman:', error);
      }
    };

    // Initialize Geoman when the map is ready
    if (mapInstance.loaded()) {
      initializeGeoman();
    } else {
      mapInstance.on('load', initializeGeoman);
    }

    return () => {
      // Remove event listeners
      mapInstance.off('load', initializeGeoman);
      mapInstance.off('gm:drawstart', handleDrawStart);
      mapInstance.off('gm:create', handleDrawEnd);
      mapInstance.off('gm:editend', handleEdit);
      mapInstance.off('gm:remove', handleRemove);

      // Clean up Geoman instance
      if (map && geomanRef.current) {
        try {
          if (map.getContainer && map.getContainer()) {
            geomanRef.current.destroy();
            geomanRef.current = null;
          }
          initializedRef.current = false;
        } catch (error) {
          console.warn('Error destroying Geoman instance:', error);
        }
      }
      geomanRef.current = null;
    };
  }, [map]); // Only depend on map, not on callbacks

  // Update event handlers when callbacks change
  useEffect(() => {
    if (!map || !geomanRef.current) return;

    const mapInstance = map.getMap();

    // Remove old event listeners
    mapInstance.off('gm:drawstart', handleDrawStart);
    mapInstance.off('gm:create', handleDrawEnd);
    mapInstance.off('gm:editend', handleEdit);
    mapInstance.off('gm:remove', handleRemove);

    // Add new event listeners
    mapInstance.on('gm:drawstart', handleDrawStart);
    mapInstance.on('gm:create', handleDrawEnd);
    mapInstance.on('gm:editend', handleEdit);
    mapInstance.on('gm:remove', handleRemove);
  }, [map, handleDrawStart, handleDrawEnd, handleEdit, handleRemove]);

  // Import editFeature when it changes
  useEffect(() => {
    console.log('editFeature', editFeature);
    if (editFeature && geomanRef.current) {
      try {
        // Clear any existing features
        geomanRef.current.features.forEach((featureData) => {
          geomanRef.current?.features.delete(featureData.id);
        });

        // Import the new editFeature
        geomanRef.current.features.importGeoJsonFeature(
          editFeature as GeoJsonImportFeature
        );

        // Fit map to the imported feature
        const mapInstance = map?.getMap();
        if (mapInstance) {
          fitMapToGeoJSON(
            mapInstance as unknown as maplibregl.Map,
            editFeature as GeoJsonImportFeature
          );
        }
      } catch (error) {
        console.warn('Error importing editFeature to Geoman:', error);
      }
    }
  }, [editFeature, map]);

  // Reset feature count when disabled
  useEffect(() => {
    if (disabled) {
      drawnFeaturesCount.current = 0;

      // Remove any existing drawn polygons when files are uploaded
      if (geomanRef.current) {
        try {
          // Remove all existing features
          geomanRef.current.features.forEach((featureData) => {
            geomanRef.current?.features.delete(featureData.id);
          });
        } catch (error) {
          console.warn(
            'Error removing existing features when disabled:',
            error
          );
        }
      }
    }
  }, [disabled]);

  return null;
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
