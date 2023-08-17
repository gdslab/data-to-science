import 'leaflet/dist/leaflet.css';
import { MapContainer } from 'react-leaflet/MapContainer';

import GeoRasterLayer from './GeoRasterLayer';
import MapLayersControl from './MapLayers';

import { setPixelColors } from './utils.tsx';

export default function Map() {
  // const pathToCOG =
  // 'https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/Q/WD/2020/7/S2A_36QWD_20200701_0_L2A/TCI.tif';
  // const pathToCOG =
  //   'https://lidar.digitalforestry.org/state/2021/carroll/carroll_2021_ortho_c.tif';
  // const pathToCOG = 'http://localhost/static/cog-webp.tif';
  // const pathToCOG = 'http://localhost/static/eb6c1243-b760-4b89-b301-bfad2abc4840.tif';
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
