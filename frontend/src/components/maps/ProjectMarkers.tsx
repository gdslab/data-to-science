import { useEffect, useRef } from 'react';
import { FeatureGroup } from 'react-leaflet';
import { Marker } from 'react-leaflet/Marker';
import { useLeafletContext } from '@react-leaflet/core';

import { DataProduct } from '../pages/projects/ProjectDetail';
import { Project } from '../pages/projects/ProjectList';
import { FeatureGroup as FG } from 'leaflet';

interface ProjectMarkersProps {
  activeProject: Project | null;
  geojsonRef: React.RefObject<L.GeoJSON>;
  projects: Project[];
  setActiveDataProduct: React.Dispatch<React.SetStateAction<DataProduct | null>>;
  setActiveProject: React.Dispatch<React.SetStateAction<Project | null>>;
}

export default function ProjectMarkers({
  activeProject,
  geojsonRef,
  projects,
  setActiveDataProduct,
  setActiveProject,
}: ProjectMarkersProps) {
  const context = useLeafletContext();
  const fgRef = useRef<FG>(null);

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
                setActiveDataProduct(null);
                setActiveProject(project);
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
