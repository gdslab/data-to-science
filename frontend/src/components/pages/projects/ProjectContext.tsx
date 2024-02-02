import axios from 'axios';
import React, { createContext, useContext, useEffect, useReducer } from 'react';
import { useParams } from 'react-router-dom';

import { Flight } from './ProjectDetail';
import { Project } from './ProjectList';
import { User } from '../../../AuthContext';

type ProjectAction = { type: string; payload: Project | null };
type FlightsAction = { type: string; payload: Flight[] | null };
type ProjectRoleAction = { type: string; payload: string | undefined };

function projectReducer(state: Project | null, action: ProjectAction) {
  switch (action.type) {
    case 'set': {
      return action.payload;
    }
    case 'clear': {
      return null;
    }
    default: {
      return state;
    }
  }
}

function projectRoleReducer(state: string | undefined, action: ProjectRoleAction) {
  switch (action.type) {
    case 'set': {
      return action.payload;
    }
    case 'clear': {
      return undefined;
    }
    default: {
      return state;
    }
  }
}

function flightsReducer(state: Flight[] | null, action: FlightsAction) {
  switch (action.type) {
    case 'set': {
      return action.payload;
    }
    case 'clear': {
      return null;
    }
    default: {
      return state;
    }
  }
}

interface Context {
  project: Project | null;
  projectDispatch: React.Dispatch<ProjectAction>;
  projectRole: string | undefined;
  projectRoleDispatch: React.Dispatch<ProjectRoleAction>;
  flights: Flight[] | null;
  flightsDispatch: React.Dispatch<FlightsAction>;
}

const context: Context = {
  project: null,
  projectDispatch: () => {},
  projectRole: undefined,
  projectRoleDispatch: () => {},
  flights: null,
  flightsDispatch: () => {},
};

const ProjectContext = createContext(context);

export function ProjectContextProvider({ children }: { children: React.ReactNode }) {
  const [project, projectDispatch] = useReducer(projectReducer, null);
  const [projectRole, projectRoleDispatch] = useReducer(projectRoleReducer, undefined);
  const [flights, flightsDispatch] = useReducer(flightsReducer, null);
  const { projectId } = useParams();

  useEffect(() => {
    async function getProject(projectId: string) {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}`
        );
        if (response) {
          projectDispatch({ type: 'set', payload: response.data });
        } else {
          projectDispatch({ type: 'clear', payload: null });
        }
      } catch {
        projectDispatch({ type: 'clear', payload: null });
      }
    }
    if (projectId && !project) getProject(projectId);
  }, [project, projectId]);

  useEffect(() => {
    async function getProjectRole(projectId: string) {
      try {
        const profile = localStorage.getItem('userProfile');
        const user: User | null = profile ? JSON.parse(profile) : null;
        if (!user) throw new Error();

        const response = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/members/${user.id}`
        );
        if (response) {
          projectRoleDispatch({ type: 'set', payload: response.data.role });
        } else {
          projectRoleDispatch({ type: 'clear', payload: undefined });
        }
      } catch {
        projectRoleDispatch({ type: 'clear', payload: undefined });
      }
    }
    if (projectId && !projectRole) getProjectRole(projectId);
  }, [projectRole, projectId]);

  useEffect(() => {
    async function getFlights(projectId: string) {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/flights`
        );
        if (response) {
          flightsDispatch({ type: 'set', payload: response.data });
        } else {
          flightsDispatch({ type: 'clear', payload: null });
        }
      } catch {
        flightsDispatch({ type: 'clear', payload: null });
      }
    }
    if (projectId && !flights) getFlights(projectId);
  }, [flights, projectId]);

  return (
    <ProjectContext.Provider
      value={{
        project,
        projectDispatch,
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
