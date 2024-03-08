import L from 'leaflet';
import { useEffect, useRef } from 'react';
import { FeatureGroup } from 'react-leaflet';
import { Marker } from 'react-leaflet/Marker';
import { useLeafletContext } from '@react-leaflet/core';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';

import { Project } from '../pages/projects/ProjectList';
import { FeatureGroup as FG } from 'leaflet';
import { useMapContext } from './MapContext';

interface ProjectMarkersProps {
  projects: Project[];
}

export default function ProjectMarkers({ projects }: ProjectMarkersProps) {
  const { activeDataProductDispatch, activeProjectDispatch, projectHoverState } =
    useMapContext();
  const context = useLeafletContext();
  const fgRef = useRef<FG>(null);

  useEffect(() => {
    // @ts-ignore
    const markers = L.markerClusterGroup();
    if (fgRef.current) {
      console.log(fgRef.current);
      fgRef.current.getLayers().forEach((marker) => {
        markers.addLayer(marker);
      });
      context.map.addLayer(markers);
    }
  }, [fgRef.current]);

  useEffect(() => {
    if (fgRef.current) {
      context.map.fitBounds(fgRef.current.getBounds(), { maxZoom: 16 });
    }
  }, [fgRef.current]);

  if (projects.length > 0) {
    return (
      <FeatureGroup ref={fgRef}>
        {projects.map((project) => (
          <Marker
            key={project.field.properties.id}
            position={[
              project.field.properties.center_y,
              project.field.properties.center_x,
            ]}
            eventHandlers={{
              click: () => {
                activeDataProductDispatch({ type: 'clear', payload: null });
                activeProjectDispatch({ type: 'set', payload: project });
              },
            }}
          />
        ))}
      </FeatureGroup>
    );
  } else {
    return null;
  }
}
