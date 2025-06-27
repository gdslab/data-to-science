import { useEffect, useMemo, useRef, useState } from 'react';
import Map, {
  MapRef,
  NavigationControl,
  ScaleControl,
} from 'react-map-gl/maplibre';
import bbox from '@turf/bbox';
import { point } from '@turf/helpers';

import IForesterControl from './IForesterControl';
import { useIForesterControlContext } from './IForesterContext';
import { useProjectContext } from '../ProjectContext';

import {
  getMapboxSatelliteBasemapStyle,
  getWorldImageryTopoBasemapStyle,
} from '../../../maps/styles/basemapStyles';
import IForesterCluster from './IForesterCluster';
import { FeatureCollection } from 'geojson';

export function getUniqueValues(
  array: (number | string)[]
): (number | string)[] {
  return Array.from(new Set(array));
}

export default function IForesterMap() {
  const [mapboxAccessToken, setMapboxAccessToken] = useState<string>('');
  const [maptilerApiKey, setMaptilerApiKey] = useState<string>('');
  const { state, dispatch } = useIForesterControlContext();
  const { activeMarkerZoom, dbhMin, dbhMax, speciesSelection } = state;
  const { iforester } = useProjectContext();

  const mapRef = useRef<MapRef | null>(null);

  // Filter IForester data based on DBH and species selection
  const filteredLocations = useMemo(() => {
    if (!iforester || iforester.length === 0) return [];
    return iforester.filter(
      ({ dbh, species }) =>
        dbh >= dbhMin &&
        dbh <= dbhMax &&
        speciesSelection.includes(species.toLowerCase())
    );
  }, [dbhMin, dbhMax, iforester, speciesSelection]);

  // Create FeatureCollection of the filtered point locations
  const filteredLocationsGeoJSON: FeatureCollection = useMemo(() => {
    return {
      type: 'FeatureCollection',
      features: filteredLocations
        .filter(({ latitude, longitude }) => latitude && longitude)
        .map(({ id, latitude, longitude }) =>
          point([longitude, latitude], { id: id })
        ),
    };
  }, [filteredLocations]);

  // Zoom to extent of filtered locations
  useEffect(() => {
    if (mapRef.current && filteredLocationsGeoJSON.features.length > 0) {
      const bounds = bbox(filteredLocationsGeoJSON);
      mapRef.current.fitBounds([bounds[0], bounds[1], bounds[2], bounds[3]], {
        padding: 20,
        duration: 1000,
      });
    }
  }, [filteredLocationsGeoJSON]);

  // Load mapbox access token and maptiler api key
  useEffect(() => {
    if (
      !import.meta.env.VITE_MAPBOX_ACCESS_TOKEN ||
      !import.meta.env.VITE_MAPTILER_API_KEY
    ) {
      fetch('/config.json')
        .then((response) => response.json())
        .then((config) => {
          if (config.mapboxAccessToken) {
            setMapboxAccessToken(config.mapboxAccessToken);
          }
          if (config.maptilerApiKey) {
            setMaptilerApiKey(config.maptilerApiKey);
          }
        })
        .catch((error) => {
          console.error('Failed to load config.json:', error);
        });
    } else {
      if (import.meta.env.VITE_MAPBOX_ACCESS_TOKEN) {
        setMapboxAccessToken(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);
      }
      if (import.meta.env.VITE_MAPTILER_API_KEY) {
        setMaptilerApiKey(import.meta.env.VITE_MAPTILER_API_KEY);
      }
    }
  }, []);

  // Set initial selected species
  useEffect(() => {
    if (iforester && iforester.length > 0 && speciesSelection.length === 0) {
      dispatch({
        type: 'SET_SPECIES_SELECTION',
        payload: getUniqueValues(
          iforester.map(({ species }) => species.toLowerCase())
        ) as string[],
      });
    }
  }, [iforester]);

  // Set initial DBH min and DBH max
  useEffect(() => {
    if (iforester && iforester.length > 0) {
      if (dbhMin === -1) {
        dispatch({
          type: 'SET_DBH_MIN',
          payload: Math.min.apply(
            Math,
            iforester.map(({ dbh }) => dbh)
          ),
        });
      }
      if (dbhMax === -1) {
        dispatch({
          type: 'SET_DBH_MAX',
          payload: Math.max.apply(
            Math,
            iforester.map(({ dbh }) => dbh)
          ),
        });
      }
    }
  }, []);

  // Zoom to active marker when activeMarkerZoom changes
  useEffect(() => {
    if (mapRef.current && activeMarkerZoom) {
      const zoomMarker = filteredLocations.filter(
        ({ id }) => id === activeMarkerZoom
      );
      if (zoomMarker.length > 0) {
        mapRef.current.flyTo({
          center: [zoomMarker[0].longitude, zoomMarker[0].latitude],
          zoom: 18,
        });
        dispatch({ type: 'SET_ACTIVE_MARKER_ZOOM', payload: '' });
      }
    }
  }, [activeMarkerZoom]);

  const mapStyle = useMemo(() => {
    return mapboxAccessToken
      ? getMapboxSatelliteBasemapStyle(mapboxAccessToken)
      : getWorldImageryTopoBasemapStyle(maptilerApiKey);
  }, [mapboxAccessToken, maptilerApiKey]);

  return (
    <Map
      ref={mapRef}
      initialViewState={{
        longitude: -86.9138040788386,
        latitude: 40.428655143949925,
        zoom: 8,
      }}
      style={{
        width: '100%',
        height: '100%',
      }}
      mapboxAccessToken={mapboxAccessToken || undefined}
      mapStyle={mapStyle}
      reuseMaps={true}
    >
      {/* Cluster markers */}
      {filteredLocations && filteredLocations.length > 0 && (
        <IForesterCluster geojsonData={filteredLocationsGeoJSON} />
      )}

      {/* Filter control */}
      <IForesterControl />

      {/* General controls */}
      <NavigationControl />
      <ScaleControl />
    </Map>
  );
}
