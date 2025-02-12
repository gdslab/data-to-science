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
      <LayersControl.BaseLayer name="USGS Topo">
        <TileLayer
          attribution="USGS The National Map: National Boundaries Dataset, 3DEP Elevation Program, Geographic Names Information System, National Hydrography Dataset, National Land Cover Database, National Structures Dataset, and National Transportation Dataset; USGS Global Ecosystems; U.S. Census Bureau TIGER/Line data; USFS Road Data; Natural Earth Data; U.S. Department of State Humanitarian Information Unit; and NOAA National Centers for Environmental Information, U.S. Coastal Relief Model. Data refreshed April, 2023."
          url="https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}"
          maxNativeZoom={16}
          maxZoom={24}
        />
      </LayersControl.BaseLayer>
      <LayersControl.BaseLayer name="USGS Imagery" checked={!mapboxAccessToken}>
        <TileLayer
          attribution="USGS The National Map: Orthoimagery. Data refreshed December, 2021."
          url="https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
          maxNativeZoom={16}
          maxZoom={24}
        />
      </LayersControl.BaseLayer>
      <LayersControl.BaseLayer name="USGS ImageryTopo">
        <TileLayer
          attribution="USGS The National Map: Orthoimagery and US Topo. Data refreshed August, 2023."
          url="https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}"
          maxNativeZoom={16}
          maxZoom={24}
        />
      </LayersControl.BaseLayer>
    </LayersControl>
  );
}
