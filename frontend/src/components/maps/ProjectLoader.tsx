import { AxiosResponse, isAxiosError } from 'axios';
import { useEffect } from 'react';

import { useMapContext } from './MapContext';
import { Project } from '../pages/projects/ProjectList';

import api from '../../api';
import { areProjectsEqual, getLocalStorageProjects } from './utils';

export default function ProjectLoader() {
  const { projectsDispatch, projectsLoadedDispatch, projects } =
    useMapContext();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const geojsonUrl = `/projects?include_all=${false}`;
        const response: AxiosResponse<Project[]> = await api.get(geojsonUrl);

        // Only update projects if they are new or differ from the current state
        if (!projects || !areProjectsEqual(projects, response.data)) {
          projectsDispatch({ type: 'set', payload: response.data });
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
      projectsDispatch({ type: 'set', payload: localStorageProjects });
      projectsLoadedDispatch({ type: 'set', payload: 'loaded' });
    } else {
      projectsLoadedDispatch({ type: 'set', payload: 'loading' });
    }
    // Always fetch latest projects from the backend
    fetchProjects();
  }, []); // Consider dependencies if projects can change elsewhere

  return null;
}
