import L from 'leaflet';
import { useEffect, useRef, useState } from 'react';
import { FeatureGroup, Popup, useMapEvents } from 'react-leaflet';
import { Marker } from 'react-leaflet/Marker';
import { useLeafletContext } from '@react-leaflet/core';
import MarkerClusterGroup from 'react-leaflet-cluster';

import { Project } from '../pages/workspace/ProjectList';
import { FeatureGroup as FG } from 'leaflet';
import { useMapContext } from './MapContext';

interface ProjectMarkersProps {
  projects: Project[];
}

export default function ProjectMarkers({ projects }: ProjectMarkersProps) {
  const { activeDataProductDispatch, activeProjectDispatch, projectsVisibleDispatch } =
    useMapContext();
  const [markers, setMarkers] = useState<L.Marker[]>([]);
  const context = useLeafletContext();
  const fgRef = useRef<FG>(null);

  useMapEvents({
    moveend(_e) {
      // update visible project markers when map moves
      let visibleProjects: string[] = [];
      if (projects.length > 0) {
        // add each project that is contained within current map to visible projects
        projects.forEach((project) => {
          const projCoordinates = L.latLng([project.centroid.y, project.centroid.x]);
          if (context.map.getBounds().contains(projCoordinates)) {
            visibleProjects.push(project.id);
          }
        });
        projectsVisibleDispatch({ type: 'set', payload: visibleProjects });
      }
    },
  });

  useEffect(() => {
    if (projects.length > 0) {
      const projectMarkers = projects.map((project) => {
        const marker = L.marker([project.centroid.y, project.centroid.x]);
        marker.on('click', () => {
          activeDataProductDispatch({ type: 'clear', payload: null });
          activeProjectDispatch({ type: 'set', payload: project });
        });
        return marker;
      });
      setMarkers(projectMarkers);
    }
  }, [projects]);

  useEffect(() => {
    if (markers.length > 0) {
      const fg = L.featureGroup(markers);
      context.map.fitBounds(fg.getBounds(), { maxZoom: 16 });
    }
  }, [markers]);

  if (projects.length > 0) {
    return (
      <FeatureGroup ref={fgRef}>
        <MarkerClusterGroup>
          {projects.map((project) => (
            <Marker
              key={project.id}
              position={[project.centroid.y, project.centroid.x]}
              eventHandlers={{
                click: () => {
                  activeDataProductDispatch({ type: 'clear', payload: null });
                  activeProjectDispatch({ type: 'set', payload: project });
                },
                mouseover: (e) => {
                  e.target.openPopup();
                },
                mouseout: (e) => {
                  e.target.closePopup();
                },
              }}
            >
              <Popup>
                <div>
                  <span className="font-bold">{project.title}</span>
                  <p>{project.description}</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MarkerClusterGroup>
      </FeatureGroup>
    );
  } else {
    return null;
  }
}
