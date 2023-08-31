import axios from 'axios';
import { MapContainer } from 'react-leaflet/MapContainer';
import { useLoaderData } from 'react-router-dom';
import 'leaflet/dist/leaflet.css';

import MapLayersControl from './MapLayersControl';
import { Project } from '../pages/projects/ProjectList';

export async function loader() {
  const response = await axios.get('/api/v1/projects');
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

export default function Map() {
  const projects = useLoaderData() as Project[];
  console.log(projects);

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
