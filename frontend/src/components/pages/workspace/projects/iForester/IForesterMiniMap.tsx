import 'leaflet/dist/leaflet.css';
import { MapContainer } from 'react-leaflet/MapContainer';
import { Marker } from 'react-leaflet/Marker';
import { Popup } from 'react-leaflet/Popup';
import { ScaleControl } from 'react-leaflet';
import { ZoomControl } from 'react-leaflet/ZoomControl';
import { useLeafletContext } from '@react-leaflet/core';

import MapLayersControl from '../../../../maps/MapLayersControl';

// updates map (loads tiles) after container size changes
const InvalidateSize = () => {
  const context = useLeafletContext();
  if (context.map) context.map.invalidateSize(true);
  return null;
};

export default function IForesterMiniMap({
  location,
  isDetailsOpen,
}: {
  location: [number, number];
  isDetailsOpen: boolean;
}) {
  return (
    <MapContainer
      className="h-48"
      center={location}
      preferCanvas={true}
      zoom={18}
      maxZoom={24}
      scrollWheelZoom={true}
      zoomControl={false}
      worldCopyJump={true}
    >
      {isDetailsOpen && <InvalidateSize />}
      <Marker position={location}>
        <Popup>
          <div className="flex flex-start gap-4">
            <span className="font-semibold text-gray-600">Latitude:</span>
            <span>{location[0].toFixed(5)}</span>
          </div>
          <div className="flex flex-start gap-4">
            <span className="font-semibold text-gray-600">Longitude:</span>
            <span>{location[1].toFixed(5)}</span>
          </div>
        </Popup>
      </Marker>
      <MapLayersControl />
      <ZoomControl position="topleft" />
      <ScaleControl position="bottomright" />
    </MapContainer>
  );
}
