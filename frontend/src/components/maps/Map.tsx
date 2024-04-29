import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect } from 'react';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ScaleControl } from 'react-leaflet';
import { ZoomControl } from 'react-leaflet/ZoomControl';

import ColorBarControl from './ColorBarControl';
import DataProductTileLayer from './DataProductTileLayer';
import MapLayersControl from './MapLayersControl';
import ProjectBoundary from './ProjectBoundary';
import ProjectMarkers from './ProjectMarkers';
import { useMapContext } from './MapContext';

import iconRetina from './icons/marker-icon-2x.png';
import icon from './icons/marker-icon.png';
import shadow from './icons/marker-shadow.png';
import PotreeViewer from './PotreeViewer';

import CompareTool, { CompareToolAlert, getFlightsWithGTIFF } from './CompareTool';

export default function Map({ layerPaneHidden }: { layerPaneHidden: boolean }) {
  const { activeDataProduct, activeMapTool, activeProject, flights, projects } =
    useMapContext();

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
        worldCopyJump={true}
      >
        {!activeProject ? <ProjectMarkers projects={projects ? projects : []} /> : null}

        {activeProject ? <ProjectBoundary project={activeProject} /> : null}

        {activeProject &&
        flights &&
        activeDataProduct &&
        activeDataProduct.data_type !== 'point_cloud' &&
        activeMapTool === 'map' ? (
          <DataProductTileLayer activeDataProduct={activeDataProduct} />
        ) : null}

        {activeProject &&
        flights &&
        activeDataProduct &&
        (activeDataProduct.data_type === 'dsm' ||
          (activeDataProduct.stac_properties &&
            activeDataProduct.stac_properties.raster.length === 1)) &&
        activeMapTool === 'map' ? (
          <ColorBarControl
            projectId={activeProject.id}
            dataProduct={activeDataProduct}
          />
        ) : null}

        {flights &&
        flights.length > 0 &&
        activeMapTool === 'compare' &&
        getFlightsWithGTIFF(flights).length > 0 ? (
          <CompareTool
            key="compare"
            flights={getFlightsWithGTIFF(flights)}
            layerPaneHidden={layerPaneHidden}
          />
        ) : activeMapTool === 'compare' && getFlightsWithGTIFF(flights).length === 0 ? (
          <CompareToolAlert />
        ) : null}

        <MapLayersControl />
        <ZoomControl position="topleft" />
        <ScaleControl position="bottomright" />
      </MapContainer>
    );
  } else {
    const copcPath = activeDataProduct.url;
    return <PotreeViewer copcPath={copcPath} />;
  }
}
