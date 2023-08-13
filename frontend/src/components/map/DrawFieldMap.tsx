import 'leaflet/dist/leaflet.css';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ZoomControl } from 'react-leaflet/ZoomControl';

import { GeomanControl } from './GeomanControl';
import MapLayersControl from './MapLayers';

export default function DrawFieldMap({ setLocation }) {
  return (
    <div className="my-4">
      <MapContainer
        center={[42.71473, -87.51332]}
        preferCanvas={true}
        zoom={6}
        minZoom={5}
        scrollWheelZoom={true}
        zoomControl={false}
        style={{ height: 400 }}
      >
        <MapLayersControl />
        <GeomanControl position="topleft" setLocation={setLocation} />
        <ZoomControl position="topleft" />
      </MapContainer>
    </div>
  );
}
