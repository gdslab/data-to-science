import { useEffect, useState } from 'react';
import { LayersControl, TileLayer } from 'react-leaflet';

import api from '../../../api';

export default function MapLayersControl() {
  const [mapboxAccessToken, setMapboxAccessToken] = useState('');

  useEffect(() => {
    async function getMapboxAccessToken() {
      try {
        const response = await api.post(`/auth/mapbox-access-token`);
        if (response && response.data && response.data.token) {
          setMapboxAccessToken(response.data.token);
        }
      } catch (err) {
        console.log('unable to fetch mapbox token');
      }
    }
    getMapboxAccessToken();
  }, []);

  return (
    <LayersControl position="topright">
      {/* Basemaps */}
      {mapboxAccessToken ? (
        <LayersControl.BaseLayer name="Mapbox Satellite Streets" checked>
          <TileLayer
            id="satellite-streets-v12"
            attribution={`© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <strong><a href="https://www.mapbox.com/map-feedback/" target="_blank">Improve this map</a></strong>`}
            url={`https://api.mapbox.com/styles/v1/mapbox/{id}/tiles/{z}/{x}/{y}?access_token=${mapboxAccessToken}`}
            maxNativeZoom={21}
            maxZoom={24}
          />
        </LayersControl.BaseLayer>
      ) : null}
      <LayersControl.BaseLayer name="OpenStreetMap">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxNativeZoom={18}
          maxZoom={24}
        />
      </LayersControl.BaseLayer>
      <LayersControl.BaseLayer
        name="ESRI World Imagery"
        checked={!mapboxAccessToken}
      >
        <TileLayer
          attribution="Esri, Maxar, Earthstar Geographics, and the GIS User Community"
          url="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxNativeZoom={16}
          maxZoom={24}
        />
      </LayersControl.BaseLayer>
    </LayersControl>
  );
}
