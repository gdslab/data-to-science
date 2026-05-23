import { AxiosResponse, isAxiosError } from 'axios';
import { useEffect } from 'react';

import { useMapContext } from './MapContext';
import { ProjectItem } from '../pages/workspace/projects/Project';

import api from '../../api';
import {
  filterValidProjects,
  getLocalStorageProjects,
  getLocalStoragePublicProjects,
  setLocalStoragePublicProjects,
} from './utils';

export default function ProjectLoader() {
  const { projectsDispatch, projectsLoadedDispatch } = useMapContext();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const [authResponse, publicResponse] = await Promise.all([
          api.get<ProjectItem[]>(`/projects?include_all=false`),
          api.get<ProjectItem[]>(`/public/projects`).catch(() => ({
            data: [] as ProjectItem[],
          })),
        ]);

        const authProjects = filterValidProjects(authResponse.data);
        const authIds = new Set(authProjects.map((p) => p.id));

        // Tag public entries and drop any that are already in the auth list
        const publicOnly = filterValidProjects(
          (publicResponse as AxiosResponse<ProjectItem[]>).data
        )
          .filter((p) => !authIds.has(p.id))
          .map((p) => ({ ...p, is_public: true }));

        setLocalStoragePublicProjects(publicOnly);

        projectsDispatch({
          type: 'set',
          payload: [...authProjects, ...publicOnly],
        });
        projectsLoadedDispatch({ type: 'set', payload: 'loaded' });
      } catch (error) {
        projectsDispatch({ type: 'set', payload: null });
        projectsLoadedDispatch({ type: 'set', payload: 'error' });
        if (isAxiosError(error)) {
          const status = error.response?.status || 500;
          const message = error.response?.data?.message || error.message;
          console.error(
            `Failed to load project geojson: ${status} -- ${message}`
          );
        } else {
          console.error('An unexpected error occurred.');
        }
      }
    };

    // Seed from cache immediately while fetch is in-flight
    const cachedAuth = getLocalStorageProjects();
    const cachedPublic = getLocalStoragePublicProjects() ?? [];
    if (cachedAuth) {
      const authIds = new Set(cachedAuth.map((p) => p.id));
      const cachedPublicFiltered = cachedPublic.filter(
        (p) => !authIds.has(p.id)
      );
      projectsDispatch({
        type: 'set',
        payload: [...cachedAuth, ...cachedPublicFiltered],
      });
      projectsLoadedDispatch({ type: 'set', payload: 'loaded' });
    } else {
      projectsLoadedDispatch({ type: 'set', payload: 'loading' });
    }

    fetchProjects();
  }, [projectsDispatch, projectsLoadedDispatch]);

  return null;
}
