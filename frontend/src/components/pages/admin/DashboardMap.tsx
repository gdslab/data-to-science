import 'maplibre-gl/dist/maplibre-gl.css';
import { useEffect, useMemo, useState } from 'react';
import Map, { NavigationControl, ScaleControl } from 'react-map-gl/maplibre';

import ProjectCluster from '../../maps/ProjectCluster';
import ProjectPopup from '../../maps/ProjectPopup';

import { PopupInfoProps } from '../../maps/HomeMap';
import {
  getMapboxSatelliteBasemapStyle,
  usgsImageryTopoBasemapStyle,
} from '../../maps/styles/basemapStyles';

export default function DashboardMap() {
  const [mapboxAccessToken, setMapboxAccessToken] = useState('');
  const [popupInfo, setPopupInfo] = useState<PopupInfoProps | null>(null);

  useEffect(() => {
    if (!import.meta.env.VITE_MAPBOX_ACCESS_TOKEN) {
      fetch('/config.json')
        .then((response) => response.json())
        .then((config) => {
          setMapboxAccessToken(config.mapboxAccessToken);
        })
        .catch((error) => {
          console.error('Failed to load config.json:', error);
        });
    } else {
      setMapboxAccessToken(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);
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
      : usgsImageryTopoBasemapStyle;
  }, [mapboxAccessToken]);

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
