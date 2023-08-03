import 'leaflet/dist/leaflet.css';
import { MapContainer } from 'react-leaflet/MapContainer';

import MapLayersControl from './MapLayers';

export default function Map() {
  return (
    <div className="flex-1">
      <MapContainer
        center={[42.71473, -87.51332]}
        preferCanvas={true}
        zoom={6}
        maxZoom={16}
        minZoom={5}
        scrollWheelZoom={true}
        zoomControl={false}
      >
        <MapLayersControl />
      </MapContainer>
    </div>
  );
}
