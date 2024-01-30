import React, { createContext, useContext, useReducer } from 'react';
import { Flight } from './ProjectDetail';
import { Project } from './ProjectList';

type ProjectAction = { type: string; payload: Project | null };
type FlightsAction = { type: string; payload: Flight[] | null };

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
  flights: Flight[] | null;
  flightsDispatch: React.Dispatch<FlightsAction>;
}

const context: Context = {
  project: null,
  projectDispatch: () => {},
  flights: null,
  flightsDispatch: () => {},
};

const ProjectContext = createContext(context);

export function ProjectContextProvider({ children }: { children: React.ReactNode }) {
  const [project, projectDispatch] = useReducer(projectReducer, null);
  const [flights, flightsDispatch] = useReducer(flightsReducer, null);

  return (
    <ProjectContext.Provider
      value={{
        project,
        projectDispatch,
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
