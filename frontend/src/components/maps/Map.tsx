import 'leaflet/dist/leaflet.css';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ZoomControl } from 'react-leaflet/ZoomControl';

import MapLayersControl from './MapLayersControl';

export default function Map() {
  return (
    <div className="flex-1">
      <MapContainer
        center={[40.428655143949925, -86.9138040788386]}
        preferCanvas={true}
        zoom={8}
        minZoom={5}
        scrollWheelZoom={true}
        zoomControl={false}
      >
        {/* <GeoRasterLayer
          zIndex={10}
          paths={[pathToCOG]}
          resolution={256}
          pixelValuesToColorFn={setPixelColors}
        /> */}
        <MapLayersControl />
        <ZoomControl position="topleft" />
      </MapContainer>
    </div>
  );
}
