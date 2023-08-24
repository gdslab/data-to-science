import 'leaflet/dist/leaflet.css';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ZoomControl } from 'react-leaflet/ZoomControl';

import GeomanControl from './GeomanControl';
import MapLayersControl from './MapLayersControl';
import { SetLocation } from './MapModal';

export default function DrawFieldMap({ setLocation }: { setLocation: SetLocation }) {
  return (
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
      <GeomanControl options={{ position: 'topright' }} setLocation={setLocation} />
      <ZoomControl position="topleft" />
    </MapContainer>
  );
}
