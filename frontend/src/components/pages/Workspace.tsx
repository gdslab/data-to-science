import axios, { AxiosResponse, isAxiosError } from 'axios';
import { Suspense } from 'react';
import {
  Await,
  isRouteErrorResponse,
  useLoaderData,
  useRouteError,
} from 'react-router-dom';

import LoadingBars from '../LoadingBars';
import ProjectList, { Project } from './projects/ProjectList';

export async function loader() {
  const endpoint = `${import.meta.env.VITE_API_V1_STR}/projects`;

  try {
    // Fetch list of user's projects
    const projects: Promise<AxiosResponse<Project[]>> = axios.get(endpoint);

    return { projects };
  } catch (error) {
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
  }
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
  const { projects } = useLoaderData() as { projects: Promise<Project[]> };

  return (
    <Suspense
      fallback={
        <div className="h-full flex justify-center items-center">
          <LoadingBars />
        </div>
      }
    >
      <Await
        resolve={projects}
        errorElement={<ErrorElement />}
        children={(resolveProjects) => <ProjectList projects={resolveProjects.data} />}
      />
    </Suspense>
  );
}
