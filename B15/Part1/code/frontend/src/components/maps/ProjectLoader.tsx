import { AxiosResponse, isAxiosError } from 'axios';
import { useContext, useEffect } from 'react';

import { useMapContext } from './MapContext';
import { ProjectItem } from '../pages/workspace/projects/Project';

import AuthContext from '../../AuthContext';
import api from '../../api';
import {
  filterValidProjects,
  getLocalStorageProjects,
  getLocalStoragePublicProjects,
  setLocalStoragePublicProjects,
} from './utils';

export default function ProjectLoader() {
  const { user } = useContext(AuthContext);
  const { projectsDispatch, projectsLoadedDispatch } = useMapContext();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        let authProjects: ProjectItem[] = [];

        if (user) {
          // Authenticated path: fetch the user's own projects
          const authResponse = await api.get<ProjectItem[]>(
            `/projects?include_all=false`
          );
          authProjects = filterValidProjects(authResponse.data);
        }

        const authIds = new Set(authProjects.map((p) => p.id));

        // Always fetch public projects (no auth required)
        const publicResponse = await api
          .get<ProjectItem[]>(`/public/projects`)
          .catch(() => ({ data: [] as ProjectItem[] }));

        // Tag public entries and drop any already in the auth list
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
            `Failed to load projects: ${status} -- ${message}`
          );
        } else {
          console.error('An unexpected error occurred.');
        }
      }
    };

    // Seed from cache immediately while fetch is in-flight
    if (user) {
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
    } else {
      // Anonymous: seed from public cache only
      const cachedPublic = getLocalStoragePublicProjects() ?? [];
      if (cachedPublic.length > 0) {
        projectsDispatch({ type: 'set', payload: cachedPublic });
        projectsLoadedDispatch({ type: 'set', payload: 'loaded' });
      } else {
        projectsLoadedDispatch({ type: 'set', payload: 'loading' });
      }
    }

    fetchProjects();
  }, [user, projectsDispatch, projectsLoadedDispatch]);

  return null;
}
