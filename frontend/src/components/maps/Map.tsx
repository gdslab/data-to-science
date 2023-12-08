import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect } from 'react';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ZoomControl } from 'react-leaflet/ZoomControl';

import DataProductTileLayer from './DataProductTileLayer';
import MapLayersControl from './MapLayersControl';
import { Project } from '../pages/projects/ProjectList';
import ProjectBoundary from './ProjectBoundary';
import ProjectMarkers from './ProjectMarkers';
import { useMapContext } from './MapContext';

import iconRetina from './icons/marker-icon-2x.png';
import icon from './icons/marker-icon.png';
import shadow from './icons/marker-shadow.png';
import PotreeViewer from './PotreeViewer';

import CompareTool, { CompareToolAlert, getFlightsWithGTIFF } from './CompareTool';

export default function Map({ projects }: { projects: Project[] }) {
  const { activeDataProduct, activeMapTool, activeProject, flights } = useMapContext();

  useEffect(() => {
    // @ts-ignore
    delete L.Icon.Default.prototype._getIconUrl;

    L.Icon.Default.mergeOptions({
      iconRetinaUrl: iconRetina,
      iconUrl: icon,
      shadowUrl: shadow,
    });
  }, []);

  if (
    !activeDataProduct ||
    (activeDataProduct && activeDataProduct.data_type !== 'point_cloud')
  ) {
    return (
      <MapContainer
        center={[40.428655143949925, -86.9138040788386]}
        preferCanvas={true}
        zoom={8}
        maxZoom={24}
        scrollWheelZoom={true}
        zoomControl={false}
      >
        {!activeProject ? <ProjectMarkers projects={projects} /> : null}
        {activeProject ? <ProjectBoundary project={activeProject} /> : null}
        {activeProject &&
        flights &&
        activeDataProduct &&
        activeDataProduct.data_type !== 'point_cloud' &&
        activeMapTool === 'map' ? (
          <DataProductTileLayer activeDataProduct={activeDataProduct} />
        ) : null}
        {flights &&
        flights.length > 0 &&
        activeMapTool === 'compare' &&
        getFlightsWithGTIFF(flights).length > 0 ? (
          <CompareTool key="compare" flights={getFlightsWithGTIFF(flights)} />
        ) : activeMapTool === 'compare' && getFlightsWithGTIFF(flights).length === 0 ? (
          <CompareToolAlert />
        ) : null}
        <MapLayersControl />
        <ZoomControl position="bottomright" />
      </MapContainer>
    );
  } else {
    return (
      <PotreeViewer eptPath={activeDataProduct.url.replace('.copc.laz', '/ept.json')} />
    );
  }
}
