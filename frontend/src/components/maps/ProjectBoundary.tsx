import axios, { AxiosResponse } from 'axios';
import { useEffect, useRef, useState } from 'react';
import { GeoJSON } from 'react-leaflet/GeoJSON';
import { useMap } from 'react-leaflet';
import { Project } from '../pages/workspace/ProjectList';

export default function ProjectBoundary({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);

  const map = useMap();
  const boundaryRef = useRef<L.GeoJSON>(null);

  useEffect(() => {
    async function fetchProject() {
      try {
        const response: AxiosResponse<Project> = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}`
        );
        if (response) {
          setProject(response.data);
        } else {
          return null;
        }
      } catch {
        console.error('Unable to fetch project');
        return null;
      }
    }
    fetchProject();
  }, [projectId]);

  useEffect(() => {
    if (boundaryRef.current) map.fitBounds(boundaryRef.current.getBounds());
  }, [boundaryRef.current]);

  return project ? (
    <GeoJSON
      ref={boundaryRef}
      style={{ fillOpacity: 0, color: '#ffffff', weight: 2 }}
      data={project.field}
    />
  ) : null;
}
