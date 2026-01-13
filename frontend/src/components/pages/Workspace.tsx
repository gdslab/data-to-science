import { AxiosResponse, isAxiosError } from 'axios';
import { useState, useEffect, useTransition } from 'react';
import { useLoaderData, useRevalidator } from 'react-router';
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from '@headlessui/react';

import ProjectList from './workspace/projects/ProjectList';
import { ProjectItem } from './workspace/projects/Project';

import api from '../../api';
import { getLocalStorageProjects } from '../maps/utils';
import { IndoorProjectAPIResponse } from './workspace/indoorProjects/IndoorProject';
import IndoorProjectList from './workspace/indoorProjects/IndoorProjectList';

export async function loader() {
  // Fetch projects from localStorage
  let cachedProjects: ProjectItem[] | null = null;
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
    .then((response: AxiosResponse<ProjectItem[]>) => {
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

  // Fecth list of user's indoor projects
  const freshIndoorProjects = api
    .get('/indoor_projects')
    .then((response: AxiosResponse<IndoorProjectAPIResponse[]>) => {
      return response;
    })
    .catch((error) => {
      if (isAxiosError(error)) {
        const status = error.response?.status || 500;
        const message = error.response?.data?.message || error.message;
        throw { status, message: `Failed to load indoor projects: ${message}` };
      } else {
        throw { status: 500, message: 'An unexpected error occurred.' };
      }
    });
  return {
    cachedProjects,
    freshProjects,
    freshIndoorProjects,
  };
}

export default function Workspace() {
  const { cachedProjects, freshProjects, freshIndoorProjects } =
    useLoaderData() as {
      cachedProjects: ProjectItem[] | null;
      freshProjects: Promise<AxiosResponse<ProjectItem[]>>;
      freshIndoorProjects: Promise<AxiosResponse<IndoorProjectAPIResponse[]>>;
    };
  const revalidator = useRevalidator();

  // Tab state
  const [selectedIndex, setSelectedIndex] = useState(0);
  // Initial indoor projects state
  const [indoorProjects, setIndoorProjects] = useState<
    IndoorProjectAPIResponse[] | null
  >(null);
  // Immediately display cached projects
  const [projects, setProjects] = useState<ProjectItem[] | null>(
    cachedProjects
  );
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

  useEffect(() => {
    // Only update if component still mounted
    let mounted = true;
    freshIndoorProjects
      .then((response) => {
        if (mounted) {
          startTransition(() => {
            setIndoorProjects(response.data);
          });
        }
      })
      .catch((error) => {
        console.error('Failed to fetch fresh projects', error);
      });
    return () => {
      mounted = false;
    };
  }, [freshIndoorProjects, startTransition]);

  return (
    <TabGroup
      className="m-4 h-[calc(100%-2rem)] flex flex-col"
      selectedIndex={selectedIndex}
      onChange={setSelectedIndex}
    >
      <TabList>
        <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-32 shrink-0 rounded-lg p-2 font-medium">
          Projects
        </Tab>
        <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-32 shrink-0 rounded-lg p-2 font-medium">
          Indoor Projects
        </Tab>
      </TabList>
      <TabPanels className="flex-1 min-h-0">
        <TabPanel className="h-full">
          <ProjectList
            projects={projects}
            revalidate={revalidator.revalidate}
          />
        </TabPanel>
        <TabPanel className="h-full">
          <IndoorProjectList indoorProjects={indoorProjects} />
        </TabPanel>
      </TabPanels>
    </TabGroup>
  );
}
