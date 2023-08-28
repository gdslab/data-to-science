import 'leaflet/dist/leaflet.css';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ZoomControl } from 'react-leaflet/ZoomControl';
import { useLeafletContext } from '@react-leaflet/core';

import GeomanControl from './GeomanControl';
import MapLayersControl from './MapLayersControl';
import { FeatureCollection, SetLocation } from './MapModal';
import UploadGeoJSON from './UploadGeoJSON';

// updates map (loads tiles) after container size changes
const InvalidateSize = () => {
  const context = useLeafletContext();
  if (context.map) context.map.invalidateSize(true);
  return null;
};

interface Props {
  featureCollection: FeatureCollection | null;
  setLocation: SetLocation;
}

export default function DrawFieldMap({ featureCollection, setLocation }: Props) {
  return (
    <MapContainer
      center={[42.71473, -87.51332]}
      preferCanvas={true}
      zoom={6}
      minZoom={5}
      maxZoom={16}
      scrollWheelZoom={true}
      zoomControl={false}
      style={{ height: 400 }}
    >
      <InvalidateSize />
      {featureCollection ? (
        <UploadGeoJSON data={featureCollection} setLocation={setLocation} />
      ) : null}
      <MapLayersControl />
      <GeomanControl options={{ position: 'topleft' }} setLocation={setLocation} />
      <ZoomControl position="topleft" />
    </MapContainer>
  );
}
