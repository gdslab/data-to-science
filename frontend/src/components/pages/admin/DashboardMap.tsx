import axios, { AxiosResponse } from 'axios';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ScaleControl } from 'react-leaflet';
import { ZoomControl } from 'react-leaflet/ZoomControl';
import { useLoaderData } from 'react-router-dom';

import ProjectMarkers from '../../maps/ProjectMarkers';
import { Project } from '../workspace/ProjectList';
import MapLayersControl from '../../maps/MapLayersControl';

export async function loader() {
  const response: AxiosResponse<Project[]> = await axios.get(
    `${import.meta.env.VITE_API_V1_STR}/projects?include_all=True`
  );
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

export default function DashboardMap() {
  const projects = useLoaderData() as Project[];

  return (
    <MapContainer
      center={[40.428655143949925, -86.9138040788386]}
      preferCanvas={true}
      zoom={8}
      maxZoom={24}
      scrollWheelZoom={true}
      zoomControl={false}
      worldCopyJump={true}
    >
      {projects && projects.length > 0 && <ProjectMarkers projects={projects} />}
      <MapLayersControl />
      <ZoomControl position="topleft" />
      <ScaleControl position="bottomright" />
    </MapContainer>
  );
}
