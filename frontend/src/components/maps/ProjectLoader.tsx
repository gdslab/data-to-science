import { AxiosResponse, isAxiosError } from 'axios';
import { useEffect } from 'react';

import { useMapContext } from './MapContext';
import { ProjectItem } from '../pages/projects/Project';

import api from '../../api';
import {
  areProjectsEqual,
  getLocalStorageProjects,
  filterValidProjects,
} from './utils';

export default function ProjectLoader() {
  const { projectsDispatch, projectsLoadedDispatch, projects } =
    useMapContext();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const geojsonUrl = `/projects?include_all=${false}`;
        const response: AxiosResponse<ProjectItem[]> = await api.get(
          geojsonUrl
        );

        // Filter out projects with invalid geographic coordinates
        const validProjects = filterValidProjects(response.data);

        // Only update projects if they are new or differ from the current state
        if (!projects || !areProjectsEqual(projects, validProjects)) {
          projectsDispatch({ type: 'set', payload: validProjects });
        }
        projectsLoadedDispatch({ type: 'set', payload: 'loaded' });
      } catch (error) {
        // Clear any previously set data and update loading state
        projectsDispatch({ type: 'set', payload: null });
        projectsLoadedDispatch({ type: 'set', payload: 'error' });
        if (isAxiosError(error)) {
          const status = error.response?.status || 500;
          const message = error.response?.data?.message || error.message;
          console.error(
            `Failed to load project geojson: ${status} -- ${message}`
          );
          // Optionally, display an error message instead of rethrowing
        } else {
          console.error('An unexpected error occurred.');
        }
      }
    };

    // Check for cached projects in local storage
    const localStorageProjects = getLocalStorageProjects();
    if (localStorageProjects) {
      // Filter cached projects as well in case they contain invalid coordinates
      const validCachedProjects = filterValidProjects(localStorageProjects);
      projectsDispatch({ type: 'set', payload: validCachedProjects });
      projectsLoadedDispatch({ type: 'set', payload: 'loaded' });
    } else {
      projectsLoadedDispatch({ type: 'set', payload: 'loading' });
    }
    // Always fetch latest projects from the backend
    fetchProjects();
  }, [projects, projectsDispatch, projectsLoadedDispatch]); // Consider dependencies if projects can change elsewhere

  return null;
}
