import axios from 'axios';
import React, { createContext, useContext, useEffect, useReducer } from 'react';
import { useParams } from 'react-router-dom';

import { ProjectMember } from './ProjectAccess';
import { Flight } from './ProjectDetail';
import { Project } from './ProjectList';
import { User } from '../../../AuthContext';

type ProjectAction = { type: string; payload: Project | null };
type ProjectMembersAction = { type: string; payload: ProjectMember[] | null };
type FlightAction = { type: string; payload: Flight | null };
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

function projectMembersReducer(
  state: ProjectMember[] | null,
  action: ProjectMembersAction
) {
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

function flightReducer(state: Flight | null, action: FlightAction) {
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
  projectMembers: ProjectMember[] | null;
  projectMembersDispatch: React.Dispatch<ProjectMembersAction>;
  projectRole: string | undefined;
  projectRoleDispatch: React.Dispatch<ProjectRoleAction>;
  flight: Flight | null;
  flightDispatch: React.Dispatch<FlightAction>;
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
  flight: null,
  flightDispatch: () => {},
  flights: null,
  flightsDispatch: () => {},
};

const ProjectContext = createContext(context);

export function ProjectContextProvider({ children }: { children: React.ReactNode }) {
  const [project, projectDispatch] = useReducer(projectReducer, null);
  const [projectMembers, projectMembersDispatch] = useReducer(
    projectMembersReducer,
    null
  );
  const [projectRole, projectRoleDispatch] = useReducer(projectRoleReducer, undefined);
  const [flight, flightDispatch] = useReducer(flightReducer, null);
  const [flights, flightsDispatch] = useReducer(flightsReducer, null);
  const { projectId, flightId } = useParams();

  useEffect(() => {
    async function getProject() {
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
    if ((projectId && !project) || (projectId && project && project.id !== projectId))
      getProject();
  }, [project, projectId]);

  useEffect(() => {
    async function getProjectMembers() {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/members`
        );
        if (response) {
          projectMembersDispatch({ type: 'set', payload: response.data });
        } else {
          projectMembersDispatch({ type: 'clear', payload: null });
        }
      } catch {
        projectMembersDispatch({ type: 'clear', payload: null });
      }
    }
    if ((projectId && !project) || (projectId && project && project.id !== projectId))
      getProjectMembers();
  }, [project, projectId, projectMembers]);

  useEffect(() => {
    async function getFlight() {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/flights/${flightId}`
        );
        if (response) {
          flightDispatch({ type: 'set', payload: response.data });
        } else {
          flightDispatch({ type: 'clear', payload: null });
        }
      } catch {
        flightDispatch({ type: 'clear', payload: null });
      }
    }

    if (
      (projectId && flightId && !flight) ||
      (flightId && flight && flight.id !== flightId)
    )
      getFlight();
  }, [flight, flightId]);

  useEffect(() => {
    async function getProjectRole() {
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
    if (
      (projectId && !projectRole) ||
      (projectId && project && project.id !== projectId)
    )
      getProjectRole();
  }, [projectRole, project, projectId]);

  useEffect(() => {
    async function getFlights() {
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
    if ((projectId && !flights) || (projectId && project && project.id !== projectId))
      getFlights();
  }, [flights, project, projectId]);

  return (
    <ProjectContext.Provider
      value={{
        project,
        projectDispatch,
        projectMembers,
        projectMembersDispatch,
        projectRole,
        projectRoleDispatch,
        flight,
        flightDispatch,
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
