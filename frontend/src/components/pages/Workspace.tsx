import axios, { AxiosResponse, isAxiosError } from 'axios';
import { Suspense, useState } from 'react';
import {
  Await,
  isRouteErrorResponse,
  useLoaderData,
  useRouteError,
} from 'react-router-dom';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';

import LoadingBars from '../LoadingBars';
import ProjectList, { Project } from './workspace/projects/ProjectList';
import { IndoorProjectAPIResponse } from './workspace/indoorProjects/IndoorProject';
import IndoorProjectList from './workspace/indoorProjects/IndoorProjectList';

export async function loader() {
  const indoorProjectsEndpoint = `${import.meta.env.VITE_API_V1_STR}/indoor_projects`;
  const projectsEndpoint = `${import.meta.env.VITE_API_V1_STR}/projects`;

  try {
    // Fetch list of user's indoor projects and uas projects
    const indoorProjects: Promise<AxiosResponse<IndoorProjectAPIResponse>> =
      axios.get(indoorProjectsEndpoint);
    const projects: Promise<AxiosResponse<Project[]>> = axios.get(projectsEndpoint);

    return { indoorProjects, projects };
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
  const [selectedIndex, setSelectedIndex] = useState(0);

  const { indoorProjects, projects } = useLoaderData() as {
    indoorProjects: Promise<IndoorProjectAPIResponse>;
    projects: Promise<Project[]>;
  };

  return (
    <TabGroup className="m-4" selectedIndex={selectedIndex} onChange={setSelectedIndex}>
      <TabList>
        <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-32 shrink-0 rounded-lg p-2 font-medium">
          Projects
        </Tab>
        <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-32 shrink-0 rounded-lg p-2 font-medium">
          Indoor Projects
        </Tab>
      </TabList>
      <TabPanels>
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
            children={(resolveProjects) => (
              <TabPanel>
                <ProjectList projects={resolveProjects.data} />
              </TabPanel>
            )}
          />
          <Await
            resolve={indoorProjects}
            errorElement={<ErrorElement />}
            children={(resolveIndoorProjects) => (
              <TabPanel>
                <IndoorProjectList indoorProjects={resolveIndoorProjects.data} />
              </TabPanel>
            )}
          />
        </Suspense>
      </TabPanels>
    </TabGroup>
  );
}
