import axios from 'axios';
import { createContext, useContext, useEffect, useReducer } from 'react';

import { DataProduct, Flight } from '../pages/projects/ProjectDetail';
import { Project } from '../pages/projects/ProjectList';

type ActiveDataProductAction = { type: string; payload: DataProduct | null };
type ActiveProjectAction = { type: string; payload: Project | null };
type FlightsAction = { type: string; payload: Flight[] };
type ProjectHoverStateAction = { type: string; payload: string | null };

function activeDataProductReducer(
  state: DataProduct | null,
  action: ActiveDataProductAction
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

function activeProjectReducer(state: Project | null, action: ActiveProjectAction) {
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

function flightsReducer(state: Flight[], action: FlightsAction) {
  switch (action.type) {
    case 'set': {
      return action.payload;
    }
    case 'clear': {
      return [];
    }
    default: {
      return state;
    }
  }
}

function projectHoverStateReducer(
  state: string | null,
  action: ProjectHoverStateAction
) {
  switch (action.type) {
    case 'set': {
      return action.payload;
    }
    case 'clear': {
      return null;
    }
    default:
      return state;
  }
}

const context: {
  activeDataProduct: DataProduct | null;
  activeDataProductDispatch: React.Dispatch<ActiveDataProductAction>;
  activeProject: Project | null;
  activeProjectDispatch: React.Dispatch<ActiveProjectAction>;
  flights: Flight[];
  projectHoverState: string | null;
  projectHoverStateDispatch: React.Dispatch<ProjectHoverStateAction>;
} = {
  activeDataProduct: null,
  activeDataProductDispatch: () => {},
  activeProject: null,
  activeProjectDispatch: () => {},
  flights: [],
  projectHoverState: null,
  projectHoverStateDispatch: () => {},
};

const MapContext = createContext(context);

export function MapContextProvider({ children }: { children: React.ReactNode }) {
  const [activeDataProduct, activeDataProductDispatch] = useReducer(
    activeDataProductReducer,
    null
  );
  const [activeProject, activeProjectDispatch] = useReducer(activeProjectReducer, null);
  const [flights, flightsDispatch] = useReducer(flightsReducer, []);
  const [projectHoverState, projectHoverStateDispatch] = useReducer(
    projectHoverStateReducer,
    null
  );

  // fetches flights for active project
  useEffect(() => {
    async function getFlights(projectId) {
      try {
        const response = await axios.get(`/api/v1/projects/${projectId}/flights`);
        if (response) {
          flightsDispatch({ type: 'set', payload: response.data });
        }
      } catch (err) {
        console.error(err);
      }
    }
    if (activeProject) {
      getFlights(activeProject.id);
    }
  }, [activeProject]);

  return (
    <MapContext.Provider
      value={{
        activeDataProduct,
        activeDataProductDispatch,
        activeProject,
        activeProjectDispatch,
        flights,
        projectHoverState,
        projectHoverStateDispatch,
      }}
    >
      {children}
    </MapContext.Provider>
  );
}

export function useMapContext() {
  return useContext(MapContext);
}
