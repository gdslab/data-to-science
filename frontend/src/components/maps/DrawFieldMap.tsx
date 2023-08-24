import 'leaflet/dist/leaflet.css';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ZoomControl } from 'react-leaflet/ZoomControl';
import { useLeafletContext } from '@react-leaflet/core';

import GeomanControl from './GeomanControl';
import MapLayersControl from './MapLayersControl';
import { SetLocation } from './MapModal';

// updates map (loads tiles) after container size changes
const InvalidateSize = () => {
  const context = useLeafletContext();
  if (context.map) context.map.invalidateSize(true);
  return null;
};

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
      <InvalidateSize />
      <MapLayersControl />
      <GeomanControl options={{ position: 'topleft' }} setLocation={setLocation} />
      <ZoomControl position="topleft" />
    </MapContainer>
  );
}
