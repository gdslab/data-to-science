import { useEffect, useRef } from 'react';
import { GeoJSON } from 'react-leaflet/GeoJSON';
import { useMap } from 'react-leaflet';
import { Project } from '../pages/projects/ProjectList';

export default function ProjectBoundary({ project }: { project: Project }) {
  const map = useMap();
  const boundaryRef = useRef<L.GeoJSON>(null);

  useEffect(() => {
    if (boundaryRef.current) map.fitBounds(boundaryRef.current.getBounds());
  }, [boundaryRef.current]);

  return (
    <GeoJSON
      ref={boundaryRef}
      style={{ fillOpacity: 0, color: '#ffffff', weight: 2 }}
      data={project.field}
    />
  );
}
