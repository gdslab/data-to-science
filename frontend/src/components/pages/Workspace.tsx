import { AxiosResponse, isAxiosError } from 'axios';
import { useState, useEffect, useTransition } from 'react';
import { useLoaderData, useRevalidator } from 'react-router-dom';

import ProjectList, { Project } from './projects/ProjectList';

import api from '../../api';
import { getLocalStorageProjects } from '../maps/utils';

export async function loader() {
  // Fetch projects from localStorage
  let cachedProjects: Project[] | null = null;
  try {
    const projectsFromCache = getLocalStorageProjects();
    if (projectsFromCache) {
      cachedProjects = projectsFromCache;
    }
  } catch (error) {
    console.error('Error reading projects from localStorage', error);
  }

  // Fetch list of user's projects
  const freshProjects = api
    .get('/projects')
    .then((response: AxiosResponse<Project[]>) => {
      // Update localStorage with latest projects
      localStorage.setItem('projects', JSON.stringify(response.data));
      return response;
    })
    .catch((error) => {
      if (isAxiosError(error)) {
        const status = error.response?.status || 500;
        const message = error.response?.data?.message || error.message;
        throw { status, message: `Failed to load projects: ${message}` };
      } else {
        throw { status: 500, message: 'An unexpected error occurred.' };
      }
    });

  return {
    cachedProjects,
    freshProjects,
  };
}

export default function Workspace() {
  const { cachedProjects, freshProjects } = useLoaderData() as {
    cachedProjects: Project[] | null;
    freshProjects: Promise<AxiosResponse<Project[]>>;
  };
  const revalidator = useRevalidator();

  // Immediately display cached projects
  const [projects, setProjects] = useState<Project[] | null>(cachedProjects);
  // Prevent interrupting user interactions with useTransition
  const [_isPending, startTransition] = useTransition();

  useEffect(() => {
    // Only update if component still mounted
    let mounted = true;
    freshProjects
      .then((response) => {
        if (mounted) {
          startTransition(() => {
            setProjects(response.data);
          });
        }
      })
      .catch((error) => {
        console.error('Failed to fetch fresh projects', error);
      });
    return () => {
      mounted = false;
    };
  }, [freshProjects, startTransition]);

  return (
    <ProjectList projects={projects} revalidate={revalidator.revalidate} />
  );
}
