import '@geoman-io/maplibre-geoman-free/dist/maplibre-geoman.css';
import 'maplibre-gl/dist/maplibre-gl.css';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useMap } from 'react-map-gl';
import {
  GeoJsonImportFeature,
  GeoJsonShapeFeature,
  Geoman,
} from '@geoman-io/maplibre-geoman-free';

import { geomanOptions } from './styles/geomanOptions';
import { GeoJSONFeature } from '../pages/projects/Project';
import { fitMapToGeoJSON } from './utils';

interface GeomanFeature {
  getGeoJson: () => GeoJsonShapeFeature;
}

interface GeomanDrawEvent {
  feature: GeomanFeature;
}

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
  const [geomanReady, setGeomanReady] = useState(false);

  const clearAllGeomanFeatures = (geoman: Geoman | null) => {
    if (!geoman) return;
    try {
      geoman.features.forEach((featureData) => {
        geoman.features.delete(featureData.id);
      });
    } catch (error) {
      console.warn('Error removing existing features:', error);
    }
  };

  // Memoize event handlers to prevent unnecessary re-renders
  const handleDrawStart = useCallback(() => {
    // Reset feature count when drawing starts (clean slate)
    drawnFeaturesCount.current = 0;

    // Remove any existing polygons when drawing starts
    clearAllGeomanFeatures(geomanRef.current);

    if (onDrawStart) {
      onDrawStart();
    }
  }, [onDrawStart]);

  const handleDrawEnd = useCallback(
    (event: GeomanDrawEvent) => {
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
    (event: GeomanDrawEvent) => {
      const feature: GeoJsonShapeFeature = event.feature.getGeoJson();

      if (onEdit) {
        onEdit(feature);
      }
    },
    [onEdit]
  );

  const handleRemove = useCallback(() => {
    // Reset feature count when polygon is removed
    drawnFeaturesCount.current = 0;

    // Call the same handler as draw start to reset formik field
    if (onDrawStart) {
      onDrawStart();
    }
  }, [onDrawStart]);

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
        setGeomanReady(true);
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
      // Remove only the load listener here; gm listeners are managed in the other effect
      mapInstance.off('load', initializeGeoman);

      // Clean up Geoman instance
      if (map && geomanRef.current) {
        try {
          if (map.getContainer && map.getContainer()) {
            geomanRef.current.destroy();
            geomanRef.current = null;
          }
          initializedRef.current = false;
          setGeomanReady(false);
        } catch (error) {
          console.warn('Error destroying Geoman instance:', error);
        }
      }
    };
  }, [map]); // Only depend on map - editFeature changes are handled by the import effect

  // Update event handlers when callbacks change
  useEffect(() => {
    if (!map || !geomanReady || !geomanRef.current) return;

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

    // Cleanup listeners on unmount or when callbacks change
    return () => {
      mapInstance.off('gm:drawstart', handleDrawStart);
      mapInstance.off('gm:create', handleDrawEnd);
      mapInstance.off('gm:editend', handleEdit);
      mapInstance.off('gm:remove', handleRemove);
    };
  }, [
    map,
    geomanReady,
    handleDrawStart,
    handleDrawEnd,
    handleEdit,
    handleRemove,
  ]);

  // Import editFeature when it changes
  useEffect(() => {
    if (editFeature && geomanReady && geomanRef.current) {
      try {
        // Clear any existing features
        clearAllGeomanFeatures(geomanRef.current);

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
  }, [editFeature, map, geomanReady]);

  // Reset feature count when disabled
  useEffect(() => {
    if (disabled) {
      drawnFeaturesCount.current = 0;

      // Remove any existing drawn polygons when files are uploaded
      clearAllGeomanFeatures(geomanRef.current);
    }
  }, [disabled]);

  return null;
}
