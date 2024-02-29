import axios, { AxiosResponse } from 'axios';
import { createContext, useContext, useEffect, useReducer } from 'react';
import { Params, useParams } from 'react-router-dom';

import { Project } from '../ProjectList';
import { ProjectMember } from '../ProjectAccess';
import { User } from '../../../../AuthContext';

import {
  FlightsAction,
  ProjectAction,
  ProjectMembersAction,
  ProjectRoleAction,
} from './actions';
import {
  flightsReducer,
  projectReducer,
  projectMembersReducer,
  projectRoleReducer,
} from './reducers';

import { Flight } from '../Project';

interface Context {
  project: Project | null;
  projectDispatch: React.Dispatch<ProjectAction>;
  projectMembers: ProjectMember[] | null;
  projectMembersDispatch: React.Dispatch<ProjectMembersAction>;
  projectRole: string | undefined;
  projectRoleDispatch: React.Dispatch<ProjectRoleAction>;
  flights: Flight[] | null;
  flightsDispatch: React.Dispatch<FlightsAction>;
}

const context: Context = {
  project: null,
  projectDispatch: () => {},
  projectMembers: null,
  projectMembersDispatch: () => {},
  projectRole: undefined,
  projectRoleDispatch: () => {},
  flights: null,
  flightsDispatch: () => {},
};

export async function getProjectMembers(
  params: Params,
  projectMembersDispatch: React.Dispatch<ProjectMembersAction>
) {
  try {
    const response: AxiosResponse<ProjectMember[]> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/members`
    );
    if (response) {
      projectMembersDispatch({ type: 'set', payload: response.data });
    } else {
      projectMembersDispatch({ type: 'clear', payload: null });
    }
  } catch (err) {
    if (axios.isAxiosError(err)) {
      console.log(err.response?.data);
    } else {
      console.error(err);
    }
    projectMembersDispatch({ type: 'clear', payload: null });
  }
}

const ProjectContext = createContext(context);

interface ProjectContextProvider {
  children: React.ReactNode;
}

export function ProjectContextProvider({ children }: ProjectContextProvider) {
  const [flights, flightsDispatch] = useReducer(flightsReducer, null);
  const [project, projectDispatch] = useReducer(projectReducer, null);
  const [projectMembers, projectMembersDispatch] = useReducer(
    projectMembersReducer,
    null
  );
  const [projectRole, projectRoleDispatch] = useReducer(projectRoleReducer, undefined);

  const params = useParams();

  useEffect(() => {
    async function getFlights() {
      try {
        const response: AxiosResponse<Flight[]> = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/flights`
        );
        if (response) {
          flightsDispatch({ type: 'set', payload: response.data });
        } else {
          flightsDispatch({ type: 'clear', payload: null });
        }
      } catch (err) {
        if (axios.isAxiosError(err)) {
          console.log(err.response?.data);
        } else {
          console.error(err);
        }
        flightsDispatch({ type: 'clear', payload: null });
      }
    }

    if (params.projectId && params.flightId) {
      getFlights();
    }
  }, [params.projectId, params.flightId]);

  useEffect(() => {
    async function getProject() {
      try {
        const response: AxiosResponse<Project> = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}`
        );
        if (response) {
          projectDispatch({ type: 'set', payload: response.data });
        } else {
          projectDispatch({ type: 'clear', payload: null });
        }
      } catch (err) {
        if (axios.isAxiosError(err)) {
          console.log(err.response?.data);
        } else {
          console.error(err);
        }
        projectDispatch({ type: 'clear', payload: null });
      }
    }

    if (params.projectId) {
      getProject();
    }
  }, [params.projectId]);

  useEffect(() => {
    if (params.projectId) {
      getProjectMembers(params, projectMembersDispatch);
    }
  }, [params.projectId]);

  useEffect(() => {
    async function getProjectRole() {
      try {
        const profile = localStorage.getItem('userProfile');
        const user: User | null = profile ? JSON.parse(profile) : null;
        if (!user) throw new Error();

        const response: AxiosResponse<ProjectMember> = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/members/${
            user.id
          }`
        );
        if (response) {
          projectRoleDispatch({ type: 'set', payload: response.data.role });
        } else {
          projectRoleDispatch({ type: 'clear', payload: undefined });
        }
      } catch (err) {
        if (axios.isAxiosError(err)) {
          console.log(err.response?.data);
        } else {
          console.error(err);
        }
        projectRoleDispatch({ type: 'clear', payload: undefined });
      }
    }

    if (params.projectId) {
      getProjectRole();
    }
  }, [params.projectId]);

  return (
    <ProjectContext.Provider
      value={{
        project,
        projectDispatch,
        projectMembers,
        projectMembersDispatch,
        projectRole,
        projectRoleDispatch,
        flights,
        flightsDispatch,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProjectContext() {
  return useContext(ProjectContext);
}
