import { AxiosResponse, isAxiosError } from 'axios';
import { Suspense } from 'react';
import {
  Await,
  isRouteErrorResponse,
  useLoaderData,
  useRouteError,
} from 'react-router-dom';

import ProjectList, { Project } from './projects/ProjectList';

import api from '../../api';
import { getLocalStorageProjects } from '../maps/utils';

export async function loader() {
  // Fetch projects from localStorage
  let cachedProjects: Project[] = [];
  try {
    // Check local storage for projects
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
        // Axios-specific error handling
        const status = error.response?.status || 500;
        const message = error.response?.data?.message || error.message;

        throw {
          status,
          message: `Failed to load projects: ${message}`,
        };
      } else {
        // Generic error handling
        throw {
          status: 500,
          message: 'An unexpected error occurred.',
        };
      }
    });

  return {
    cachedProjects,
    freshProjects,
  };
}

type LoaderError = {
  status: number;
  message: string;
};

function ErrorElement() {
  const error = useRouteError() as LoaderError;

  // Check if structured as a route error response
  if (isRouteErrorResponse(error)) {
    return (
      <div className="h-full flex flex-col justify-center items-center">
        <h1>Error {error.status}</h1>
        <p>{error.data.message}</p>
      </div>
    );
  }

  // Fallback for unexpected errors
  return (
    <div className="h-full flex flex-col justify-center items-center">
      <h1>Unexpected Error</h1>
      <p>{error?.message || 'Something went wrong!'}</p>
    </div>
  );
}

export default function Workspace() {
  const { cachedProjects, freshProjects } = useLoaderData() as {
    cachedProjects: Project[];
    freshProjects: Promise<AxiosResponse<Project[]>>;
  };

  return (
    <Suspense fallback={<ProjectList projects={cachedProjects} />}>
      <Await
        resolve={freshProjects}
        errorElement={<ErrorElement />}
        children={(resolveProjects) => (
          <ProjectList projects={resolveProjects.data} />
        )}
      />
    </Suspense>
  );
}
