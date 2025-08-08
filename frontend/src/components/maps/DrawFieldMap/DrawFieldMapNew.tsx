import { useFormikContext } from 'formik';
import { FeatureCollection } from 'geojson';
import { useEffect, useMemo, useState, useRef } from 'react';
import bbox from '@turf/bbox';

import GeomanControl from '../GeomanControl';
import Map, {
  GeolocateControl,
  NavigationControl,
  ScaleControl,
  Source,
  Layer,
  MapRef,
} from 'react-map-gl/maplibre';

import {
  getMapboxSatelliteBasemapStyle,
  getWorldImageryTopoBasemapStyle,
  osmBasemapStyle,
} from '../styles/basemapStyles';

interface Props {
  featureCollection: FeatureCollection | null;
  isUpdate?: boolean;
  mapboxAccessToken?: string;
  maptilerApiKey?: string;
  setFeatureCollection: React.Dispatch<
    React.SetStateAction<FeatureCollection | null>
  >;
  featureLimit?: number;
  onDrawStart?: () => void;
  onDrawEnd?: (feature: any) => void;
}

export default function DrawFieldMapNew({
  featureCollection,
  isUpdate = false,
  mapboxAccessToken = '',
  maptilerApiKey = '',
  setFeatureCollection,
  featureLimit = 1,
  onDrawStart,
  onDrawEnd,
}: Props) {
  const [config, setConfig] = useState<{ osmLabelFilter?: string } | null>(
    null
  );
  const [selectedFeature, setSelectedFeature] = useState<any>(null);
  const [drawnFeature, setDrawnFeature] = useState<any>(null);
  const mapRef = useRef<MapRef>(null);
  const { setFieldValue, setFieldTouched } = useFormikContext();

  // Load config for osmLabelFilter
  useEffect(() => {
    fetch('/config.json')
      .then((response) => response.json())
      .then((loadedConfig) => {
        setConfig({ osmLabelFilter: loadedConfig.osmLabelFilter });
      })
      .catch((error) => {
        console.error('Failed to load config.json:', error);
        setConfig({}); // Set empty config on error
      });
  }, []);

  // Zoom to feature collection when it changes
  useEffect(() => {
    if (featureCollection && mapRef.current) {
      try {
        const bounds = bbox(featureCollection);
        mapRef.current.fitBounds(
          [
            [bounds[0], bounds[1]], // southwest
            [bounds[2], bounds[3]], // northeast
          ],
          {
            padding: 50,
            duration: 1000,
          }
        );
      } catch (error) {
        console.error('Error fitting bounds to feature collection:', error);
      }
    }
  }, [featureCollection]);

  // Handle draw start - reinitialize formik location field and clear uploaded features
  const handleDrawStart = () => {
    // Clear the formik location field
    setFieldValue('location', null);
    setFieldTouched('location', true);

    // Clear uploaded feature collection
    setFeatureCollection(null);

    // Clear drawn feature
    setDrawnFeature(null);

    // Call parent callback if provided
    if (onDrawStart) {
      onDrawStart();
    }
  };

  // Handle draw end - update formik location field with drawn feature
  const handleDrawEnd = (feature: any) => {
    // Convert MultiPolygon to Polygon if needed
    let convertedFeature = feature;
    if (feature.geometry.type === 'MultiPolygon') {
      convertedFeature = {
        ...feature,
        geometry: {
          type: 'Polygon',
          coordinates: feature.geometry.coordinates[0], // Take the first polygon
        },
      };
    }

    // Update drawn feature state
    setDrawnFeature(convertedFeature);

    // Update formik location field
    setFieldValue('location', convertedFeature);
    setFieldTouched('location', true);

    // Call parent callback if provided
    if (onDrawEnd) {
      onDrawEnd(convertedFeature);
    }
  };

  // Clear drawn features when feature collection changes (file upload)
  useEffect(() => {
    if (featureCollection) {
      // Clear drawn feature when file is uploaded
      setDrawnFeature(null);

      // Clear formik location field to allow selection from uploaded features
      setFieldValue('location', null);
      setFieldTouched('location', true);
    }
  }, [featureCollection, setFieldValue, setFieldTouched]);

  // Add click event handler for GeoJSON features
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const handleMapClick = (event: any) => {
      const features = map.queryRenderedFeatures(event.point, {
        layers: ['feature-collection-layer', 'feature-collection-border-layer'],
      });

      if (features.length > 0) {
        setSelectedFeature(features[0]);

        // Set the selected feature as the form's location field
        setFieldValue('location', features[0]);
        setFieldTouched('location', true);
      } else {
        // Clicked outside of features, deselect
        setSelectedFeature(null);
      }
    };

    map.on('click', handleMapClick);

    return () => {
      map.off('click', handleMapClick);
    };
  }, [featureCollection, setFieldValue, setFieldTouched]);

  // Create layer definitions with dynamic styling based on selection
  const featureCollectionLayer = useMemo(
    () => ({
      id: 'feature-collection-layer',
      type: 'fill' as const,
      source: 'feature-collection-source',
      paint: {
        'fill-color': '#3388ff',
        'fill-opacity': 0.3,
      },
    }),
    []
  );

  const featureCollectionBorderLayer = useMemo(
    () => ({
      id: 'feature-collection-border-layer',
      type: 'line' as const,
      source: 'feature-collection-source',
      paint: {
        'line-color': [
          'case',
          ['==', ['get', 'id'], selectedFeature?.properties?.id || ''],
          '#ff4444', // Red for selected feature
          '#3388ff', // Blue for unselected features
        ] as any,
        'line-width': [
          'case',
          ['==', ['get', 'id'], selectedFeature?.properties?.id || ''],
          4, // Thicker line for selected feature
          2, // Normal width for unselected features
        ] as any,
      },
    }),
    [selectedFeature]
  );

  const mapStyle = useMemo(() => {
    if (mapboxAccessToken) {
      return getMapboxSatelliteBasemapStyle(mapboxAccessToken);
    } else if (maptilerApiKey) {
      return getWorldImageryTopoBasemapStyle(
        maptilerApiKey,
        config || undefined
      );
    } else {
      // Fallback to OSM basemap style which includes glyphs
      return osmBasemapStyle;
    }
  }, [mapboxAccessToken, maptilerApiKey, config]);

  return (
    <Map
      ref={mapRef}
      key={`${mapboxAccessToken ? 'mapbox' : 'maptiler'}-${
        maptilerApiKey ? 'with-labels' : 'no-labels'
      }`}
      initialViewState={{
        longitude: -86.9138040788386,
        latitude: 40.428655143949925,
      }}
      style={{ width: '100%', height: '100%' }}
      mapboxAccessToken={mapboxAccessToken || undefined}
      mapStyle={mapStyle}
    >
      {/* Render GeoJSON feature collection if it exists */}
      {featureCollection && (
        <Source
          id="feature-collection-source"
          type="geojson"
          data={featureCollection}
        >
          <Layer {...featureCollectionLayer} />
          <Layer {...featureCollectionBorderLayer} />
        </Source>
      )}

      {/* Controls */}
      <GeomanControl
        onDrawStart={handleDrawStart}
        onDrawEnd={handleDrawEnd}
        featureLimit={featureLimit}
        disabled={!!featureCollection} // Disable drawing when files are uploaded
      />
      <GeolocateControl position="top-left" />
      <NavigationControl />
      <ScaleControl position="bottom-right" />
    </Map>
  );
}
