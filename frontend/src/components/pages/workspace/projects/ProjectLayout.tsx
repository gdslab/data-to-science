import { useEffect, useRef } from 'react';
import { Outlet, Params, useLoaderData } from 'react-router';

import ProjectBreadcrumbs from './Breadcrumbs';
import ProjectContextProvider, { useProjectContext } from './ProjectContext';
import FieldCampaignContextProvider from './fieldCampaigns/FieldCampaignContext';
import FlightContextProvider from './FlightContext';
import { Flight, ProjectDetail, ProjectModule } from './Project';
import { ProjectMember } from './ProjectAccess';
import { Team } from '../../teams/Teams';
import { User } from '../../../../AuthContext';

import api from '../../../../api';

export type ProjectLayoutData = {
  project: ProjectDetail | null;
  role: string | null;
  flights: Flight[];
  project_members: ProjectMember[];
  project_modules: ProjectModule[];
  teams: Team[];
};

/**
 * Loader for project-specific routes (routes with :projectId).
 * This loader runs when entering any /projects/:projectId/* route.
 */
export async function loader({ params }: { params: Params<string> }) {
  const profile = localStorage.getItem('userProfile');
  const user: User | null = profile ? JSON.parse(profile) : null;
  if (!user) {
    return {
      project: null,
      role: null,
      flights: [],
      project_members: [],
      project_modules: [],
      teams: [],
    };
  }

  try {
    const [project, projectMember, flights, projectMembers, projectModules, teams] =
      await Promise.all([
        api.get(`/projects/${params.projectId}`),
        api.get(`/projects/${params.projectId}/members/${user.id}`),
        api.get(`/projects/${params.projectId}/flights`),
        api.get(`/projects/${params.projectId}/members`),
        api.get(`/projects/${params.projectId}/modules`),
        api.get('/teams', { params: { owner_only: true } }),
      ]);

    if (project && projectMember && flights && projectMembers && projectModules && teams) {
      const teamsData = teams.data as Team[];
      teamsData.unshift({
        title: 'No team',
        id: '',
        is_owner: false,
        description: '',
        exts: [],
      });

      return {
        project: project.data,
        role: projectMember.data.role,
        flights: flights.data,
        project_members: projectMembers.data,
        project_modules: projectModules.data,
        teams: teamsData,
      };
    } else {
      return {
        project: null,
        role: null,
        flights: [],
        project_members: [],
        project_modules: [],
        teams: [],
      };
    }
  } catch {
    return {
      project: null,
      role: null,
      flights: [],
      project_members: [],
      project_modules: [],
      teams: [],
    };
  }
}

/**
 * Wrapper component for project-specific routes.
 * Handles loading project data into context and passing it to children.
 */
export function ProjectOutlet() {
  const loaderData = useLoaderData() as ProjectLayoutData;

  const {
    projectDispatch,
    projectRoleDispatch,
    projectMembersDispatch,
    projectModulesDispatch,
    flightsDispatch,
    flightsFilterSelectionDispatch,
    flights: contextFlights,
  } = useProjectContext();

  const flightsLoaderRef = useRef<Flight[] | null>(null);

  // Set project data into context when loader data is available
  useEffect(() => {
    if (loaderData?.project) {
      projectDispatch({ type: 'set', payload: loaderData.project });
    }
  }, [loaderData?.project, projectDispatch]);

  useEffect(() => {
    if (loaderData?.role) {
      projectRoleDispatch({ type: 'set', payload: loaderData.role });
    }
  }, [loaderData?.role, projectRoleDispatch]);

  useEffect(() => {
    if (loaderData?.project_modules) {
      projectModulesDispatch({
        type: 'set',
        payload: loaderData.project_modules,
      });
    }
  }, [loaderData?.project_modules, projectModulesDispatch]);

  useEffect(() => {
    if (loaderData?.project_members) {
      projectMembersDispatch({
        type: 'set',
        payload: loaderData.project_members,
      });
    }
  }, [loaderData?.project_members, projectMembersDispatch]);

  useEffect(() => {
    const flights = loaderData?.flights;
    if (flights && flightsLoaderRef.current !== flights) {
      flightsLoaderRef.current = flights;
      flightsDispatch({ type: 'set', payload: flights });

      // Initialize filter selection
      if (contextFlights) {
        if (contextFlights.length === 0) {
          flightsFilterSelectionDispatch({
            type: 'set',
            payload: [...new Set(flights.map(({ sensor }) => sensor))],
          });
        }
      } else {
        flightsFilterSelectionDispatch({
          type: 'set',
          payload: [...new Set(flights.map(({ sensor }) => sensor))],
        });
      }
    }
  }, [
    loaderData?.flights,
    flightsDispatch,
    flightsFilterSelectionDispatch,
    contextFlights,
  ]);

  return <Outlet context={loaderData} />;
}

/**
 * Main layout component for all /projects/* routes.
 * Provides context providers, breadcrumbs, and renders children via Outlet.
 */
export default function ProjectLayout() {
  return (
    <ProjectContextProvider>
      <FlightContextProvider>
        <FieldCampaignContextProvider>
          <div className="h-full flex flex-col">
            <div className="p-4">
              <ProjectBreadcrumbs />
            </div>
            <div className="grow min-h-0">
              <Outlet />
            </div>
          </div>
        </FieldCampaignContextProvider>
      </FlightContextProvider>
    </ProjectContextProvider>
  );
}
