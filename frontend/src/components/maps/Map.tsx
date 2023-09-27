import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect, useRef } from 'react';
import { GeoJSON } from 'react-leaflet/GeoJSON';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ZoomControl } from 'react-leaflet/ZoomControl';

import GeoRasterLayer from './GeoRasterLayer';
import MapLayersControl from './MapLayersControl';
import { Project } from '../pages/projects/ProjectList';
import ProjectMarkers from './ProjectMarkers';
import { useMapContext } from './MapContext';

import iconRetina from './icons/marker-icon-2x.png';
import icon from './icons/marker-icon.png';
import shadow from './icons/marker-shadow.png';

export default function Map({ projects }: { projects: Project[] }) {
  const { activeDataProduct, activeProject, flights, geoRasterId, symbologySettings } =
    useMapContext();

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

  return (
    <MapContainer
      center={[40.428655143949925, -86.9138040788386]}
      preferCanvas={true}
      zoom={8}
      maxZoom={18}
      scrollWheelZoom={true}
      zoomControl={false}
    >
      {!activeProject ? (
        <ProjectMarkers projects={projects} geojsonRef={activeProjectRef} />
      ) : null}
      {activeProject ? (
        <GeoJSON
          key={activeProject.id}
          ref={activeProjectRef}
          style={{ fillOpacity: 0, color: '#23ccff' }}
          data={activeProject.field}
        />
      ) : null}
      {activeProject && flights && activeDataProduct ? (
        <GeoRasterLayer
          key={geoRasterId}
          zIndex={10}
          paths={[activeDataProduct.url]}
          resolution={256}
          activeDataProduct={activeDataProduct}
          symbologySettings={symbologySettings}
        />
      ) : null}
      <MapLayersControl />
      <ZoomControl position="bottomright" />
    </MapContainer>
  );
}
