import 'maplibre-gl/dist/maplibre-gl.css';
import { useEffect, useMemo, useState } from 'react';
import Map, { NavigationControl, ScaleControl } from 'react-map-gl/maplibre';

import ProjectCluster from '../../maps/ProjectCluster';
import ProjectPopup from '../../maps/ProjectPopup';

import { PopupInfoProps } from '../../maps/HomeMap';
import {
  getMapboxSatelliteBasemapStyle,
  getWorldImageryTopoBasemapStyle,
} from '../../maps/styles/basemapStyles';

export default function DashboardMap() {
  const [mapboxAccessToken, setMapboxAccessToken] = useState('');
  const [maptilerApiKey, setMaptilerApiKey] = useState('');
  const [popupInfo, setPopupInfo] = useState<PopupInfoProps | null>(null);
  const [config, setConfig] = useState<{ osmLabelFilter?: string } | null>(
    null
  );

  useEffect(() => {
    if (
      !import.meta.env.VITE_MAPBOX_ACCESS_TOKEN ||
      !import.meta.env.VITE_MAPTILER_API_KEY
    ) {
      fetch('/config.json')
        .then((response) => response.json())
        .then((loadedConfig) => {
          if (loadedConfig.mapboxAccessToken) {
            setMapboxAccessToken(loadedConfig.mapboxAccessToken);
          }
          if (loadedConfig.maptilerApiKey) {
            setMaptilerApiKey(loadedConfig.maptilerApiKey);
          }
          setConfig({ osmLabelFilter: loadedConfig.osmLabelFilter });
        })
        .catch((error) => {
          console.error('Failed to load config.json:', error);
          setConfig({}); // Set empty config on error
        });
    } else {
      if (import.meta.env.VITE_MAPBOX_ACCESS_TOKEN) {
        setMapboxAccessToken(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);
      }
      if (import.meta.env.VITE_MAPTILER_API_KEY) {
        setMaptilerApiKey(import.meta.env.VITE_MAPTILER_API_KEY);
      }
      // Still need to load config for osmLabelFilter even if using env vars
      fetch('/config.json')
        .then((response) => response.json())
        .then((loadedConfig) => {
          setConfig({ osmLabelFilter: loadedConfig.osmLabelFilter });
        })
        .catch((error) => {
          console.error('Failed to load config.json:', error);
          setConfig({}); // Set empty config on error
        });
    }
  }, []);

  const handleMapClick = (event) => {
    const map: maplibregl.Map = event.target;

    if (map.getLayer('unclustered-point')) {
      const features = map.queryRenderedFeatures(event.point, {
        layers: ['unclustered-point'],
      });

      if (features.length > 0) {
        const clickedFeature = features[0];
        const clickedFeatureType = clickedFeature.geometry.type.toLowerCase();

        if (clickedFeature.geometry.type === 'Point') {
          const coordinates = clickedFeature.geometry.coordinates;

          setPopupInfo({
            feature: clickedFeature,
            feature_type: clickedFeatureType,
            latitude: coordinates[1],
            longitude: coordinates[0],
          });
        }
      }
    }
  };

  const handlePopupClose = () => setPopupInfo(null);

  const mapStyle = useMemo(() => {
    return mapboxAccessToken
      ? getMapboxSatelliteBasemapStyle(mapboxAccessToken)
      : getWorldImageryTopoBasemapStyle(maptilerApiKey, config || undefined);
  }, [mapboxAccessToken, maptilerApiKey, config]);

  return (
    <Map
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
      maxZoom={26}
      reuseMaps={true}
      onClick={handleMapClick}
    >
      {/* Display marker cluster for all project centroids */}
      <ProjectCluster fetchFromAPI={true} includeAll={true} />

      {/* Display popup when unclustered project marker clicked on */}
      {popupInfo && (
        <ProjectPopup
          onClose={handlePopupClose}
          popupInfo={popupInfo}
          showActionButton={false}
        />
      )}

      {/* General Controls */}
      <NavigationControl />
      <ScaleControl />
    </Map>
  );
}
