import axios from 'axios';
import { useEffect, useRef, useState } from 'react';
import { GeoJSON } from 'react-leaflet/GeoJSON';
import { MapContainer } from 'react-leaflet/MapContainer';
import { useLoaderData } from 'react-router-dom';
import 'leaflet/dist/leaflet.css';
import { ZoomControl } from 'react-leaflet/ZoomControl';
import L from 'leaflet';

import { DataProduct } from '../pages/projects/ProjectDetail';
import { Flight } from '../pages/projects/ProjectDetail';
import FlightControl from './FlightControl';
import GeoRasterLayer from './GeoRasterLayer';
import MapLayersControl from './MapLayersControl';
import { Project } from '../pages/projects/ProjectList';
import ProjectMarkers from './ProjectMarkers';

import iconRetina from './icons/marker-icon-2x.png';
import icon from './icons/marker-icon.png';
import shadow from './icons/marker-shadow.png';

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

  const [colorRamp, setColorRamp] = useState('Spectral');
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [activeDataProduct, setActiveDataProduct] = useState<DataProduct | null>(null);
  const [flights, setFlights] = useState<Flight[] | null>(null);

  const activeProjectRef = useRef<L.GeoJSON>(null);

  useEffect(() => {
    // @ts-ignore
    delete L.Icon.Default.prototype._getIconUrl;

    L.Icon.Default.mergeOptions({
      iconRetinaUrl: iconRetina,
      iconUrl: icon,
      shadowUrl: shadow,
    });
  }, []);

  useEffect(() => {
    if (activeProject) {
      getFlights(activeProject.id);
    }
    async function getFlights(projectId) {
      try {
        const response = await axios.get(`/api/v1/projects/${projectId}/flights`);
        if (response) {
          setFlights(response.data);
        }
      } catch (err) {
        console.error(err);
      }
    }
  }, [activeProject]);

  return (
    <MapContainer
      center={[40.428655143949925, -86.9138040788386]}
      preferCanvas={true}
      zoom={8}
      maxZoom={20}
      scrollWheelZoom={true}
      zoomControl={false}
    >
      <ProjectMarkers
        {...{ activeProject, projects, setActiveDataProduct, setActiveProject }}
        geojsonRef={activeProjectRef}
      />
      {activeProject ? (
        <GeoJSON
          key={activeProject.id}
          ref={activeProjectRef}
          data={activeProject.field}
        />
      ) : null}
      {activeProject && flights ? (
        <FlightControl
          {...{
            activeDataProduct,
            colorRamp,
            flights,
            setActiveDataProduct,
            setColorRamp,
          }}
          project={activeProject}
        />
      ) : null}
      {activeProject && flights && activeDataProduct ? (
        <GeoRasterLayer
          key={`${activeDataProduct.id}-${colorRamp}`}
          zIndex={10}
          paths={[activeDataProduct.url]}
          resolution={256}
          bandInfo={activeDataProduct.band_info.bands}
          colorRamp={colorRamp}
        />
      ) : null}
      {/* <MapLayersControl /> */}
      <ZoomControl position="topleft" />
    </MapContainer>
  );
}
