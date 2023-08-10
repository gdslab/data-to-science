import 'leaflet/dist/leaflet.css';
import { MapContainer } from 'react-leaflet/MapContainer';

import GeoRasterLayer from './GeoRasterLayer';
import MapLayersControl from './MapLayers';

import { setPixelColors } from './utils.tsx';

export default function Map() {
  return (
    <div className="flex-1">
      <MapContainer
        center={[42.71473, -87.51332]}
        preferCanvas={true}
        zoom={6}
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
      </MapContainer>
    </div>
  );
}
