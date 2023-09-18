import L from 'leaflet';
import { useEffect, useRef } from 'react';
import { FeatureGroup } from 'react-leaflet';
import { Marker } from 'react-leaflet/Marker';
import { useLeafletContext } from '@react-leaflet/core';
import 'leaflet.smooth_marker_bouncing';

import { Project } from '../pages/projects/ProjectList';
import { FeatureGroup as FG } from 'leaflet';
import { useMapContext } from './MapContext';

interface ProjectMarkersProps {
  geojsonRef: React.RefObject<L.GeoJSON>;
  projects: Project[];
}

export default function ProjectMarkers({ geojsonRef, projects }: ProjectMarkersProps) {
  const {
    activeDataProductDispatch,
    activeProject,
    activeProjectDispatch,
    projectHoverState,
  } = useMapContext();
  const context = useLeafletContext();
  const fgRef = useRef<FG>(null);

  useEffect(() => {
    // @ts-ignore
    L.Marker.stopAllBouncingMarkers();
    if (fgRef.current) {
      let bounceMarkerIdx = -1;
      if (projectHoverState) {
        bounceMarkerIdx = projects
          .map((project) => project.id)
          .indexOf(projectHoverState);
      }
      if (bounceMarkerIdx > -1) {
        // @ts-ignore
        fgRef.current.getLayers()[bounceMarkerIdx].bounce();
      }
    }
  }, [projectHoverState]);

  useEffect(() => {
    if (fgRef.current) {
      context.map.fitBounds(fgRef.current.getBounds(), { maxZoom: 16 });
    }
  }, [fgRef.current]);

  useEffect(() => {
    if (geojsonRef.current) {
      context.map.fitBounds(geojsonRef.current.getBounds(), { maxZoom: 16 });
    }
  }, [activeProject]);

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
