import axios from 'axios';
import { createContext, useContext, useEffect, useReducer } from 'react';
import { v4 as uuidv4 } from 'uuid';

import { DataProduct, Flight } from '../pages/projects/ProjectDetail';
import { Project } from '../pages/projects/ProjectList';

export interface DSMSymbologySettings {
  colorRamp: string;
  max: number;
  meanStdDev: number;
  min: number;
  mode: string;
  userMin: number;
  userMax: number;
}

export interface OrthoSymbologySettings {
  mode: string;
  meanStdDev: number;
  red: {
    idx: number;
    min: number;
    max: number;
    userMin: number;
    userMax: number;
  };
  green: {
    idx: number;
    min: number;
    max: number;
    userMin: number;
    userMax: number;
  };
  blue: {
    idx: number;
    min: number;
    max: number;
    userMin: number;
    userMax: number;
  };
}

export type MapTool = 'map' | 'compare' | 'timeline';

export type SymbologySettings = DSMSymbologySettings | OrthoSymbologySettings;

const defaultSymbologySettings = {
  colorRamp: 'rainbow',
  max: 255,
  meanStdDev: 2,
  min: 0,
  mode: 'minMax',
  userMin: 0,
  userMax: 255,
};

type ActiveDataProductAction = {
  type: string;
  payload: DataProduct | Partial<DataProduct> | null;
};
type ActiveMapToolAction = { type: string; payload: MapTool };
type ActiveProjectAction = { type: string; payload: Project | null };
type FlightsAction = { type: string; payload: Flight[] };
type GeoRasterIdAction = { type: string };
type ProjectHoverStateAction = { type: string; payload: string | null };
export type SymbologySettingsAction = { type: string; payload: SymbologySettings };
type TileScaleAction = { type: string; payload: number };

function activeDataProductReducer(
  state: DataProduct | null,
  action: ActiveDataProductAction
) {
  switch (action.type) {
    case 'set': {
      return action.payload as DataProduct;
    }
    case 'update': {
      if (state && action.payload) {
        const updatedDataProduct = { ...state, ...action.payload } as DataProduct;
        return updatedDataProduct;
      }
      return state;
    }
    case 'clear': {
      return null;
    }
    default: {
      return state;
    }
  }
}

function activeMapToolReducer(state: MapTool, action: ActiveMapToolAction) {
  switch (action.type) {
    case 'set': {
      return action.payload;
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

function geoRasterIdReducer(state: string, action: GeoRasterIdAction) {
  switch (action.type) {
    case 'create': {
      return uuidv4();
    }
    case 'remove': {
      return '';
    }
    default:
      return state;
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

function symbologySettingsReducer(
  state: SymbologySettings,
  action: SymbologySettingsAction
) {
  switch (action.type) {
    case 'update': {
      return action.payload;
    }
    default:
      return state;
  }
}

function tileScaleReducer(state: number, action: TileScaleAction) {
  switch (action.type) {
    case 'set': {
      if (action.payload > 0 && action.payload < 5) {
        return action.payload;
      } else {
        return 2;
      }
    }
    default:
      return state;
  }
}

const context: {
  activeDataProduct: DataProduct | null;
  activeDataProductDispatch: React.Dispatch<ActiveDataProductAction>;
  activeMapTool: MapTool;
  activeMapToolDispatch: React.Dispatch<ActiveMapToolAction>;
  activeProject: Project | null;
  activeProjectDispatch: React.Dispatch<ActiveProjectAction>;
  flights: Flight[];
  geoRasterId: string;
  geoRasterIdDispatch: React.Dispatch<GeoRasterIdAction>;
  projectHoverState: string | null;
  projectHoverStateDispatch: React.Dispatch<ProjectHoverStateAction>;
  symbologySettings: SymbologySettings;
  symbologySettingsDispatch: React.Dispatch<SymbologySettingsAction>;
  tileScale: number;
  tileScaleDispatch: React.Dispatch<TileScaleAction>;
} = {
  activeDataProduct: null,
  activeDataProductDispatch: () => {},
  activeMapTool: 'map',
  activeMapToolDispatch: () => {},
  activeProject: null,
  activeProjectDispatch: () => {},
  flights: [],
  geoRasterId: '',
  geoRasterIdDispatch: () => {},
  projectHoverState: null,
  projectHoverStateDispatch: () => {},
  symbologySettings: defaultSymbologySettings,
  symbologySettingsDispatch: () => {},
  tileScale: 2,
  tileScaleDispatch: () => {},
};

const MapContext = createContext(context);

export function MapContextProvider({ children }: { children: React.ReactNode }) {
  const [activeDataProduct, activeDataProductDispatch] = useReducer(
    activeDataProductReducer,
    null
  );
  const [activeMapTool, activeMapToolDispatch] = useReducer(
    activeMapToolReducer,
    'map'
  );
  const [activeProject, activeProjectDispatch] = useReducer(activeProjectReducer, null);
  const [flights, flightsDispatch] = useReducer(flightsReducer, []);
  const [geoRasterId, geoRasterIdDispatch] = useReducer(geoRasterIdReducer, '');
  const [projectHoverState, projectHoverStateDispatch] = useReducer(
    projectHoverStateReducer,
    null
  );
  const [symbologySettings, symbologySettingsDispatch] = useReducer(
    symbologySettingsReducer,
    defaultSymbologySettings
  );
  const [tileScale, tileScaleDispatch] = useReducer(tileScaleReducer, 2);

  async function getFlights(projectId) {
    try {
      const response = await axios.get(
        `/api/v1/projects/${projectId}/flights?include_all=false`
      );
      if (response) {
        flightsDispatch({ type: 'set', payload: response.data });
      }
    } catch (err) {
      console.log('Unable to fetch flights');
    }
  }

  // fetches flights for active project
  useEffect(() => {
    if (activeProject) {
      getFlights(activeProject.id);
    }
  }, [activeProject]);

  // update flights/data products to check for changes to saved styles
  useEffect(() => {
    if (activeDataProduct && activeProject) {
      getFlights(activeProject.id);
    }
  }, [activeDataProduct]);

  return (
    <MapContext.Provider
      value={{
        activeDataProduct,
        activeDataProductDispatch,
        activeMapTool,
        activeMapToolDispatch,
        activeProject,
        activeProjectDispatch,
        flights,
        geoRasterId,
        geoRasterIdDispatch,
        projectHoverState,
        projectHoverStateDispatch,
        symbologySettings,
        symbologySettingsDispatch,
        tileScale,
        tileScaleDispatch,
      }}
    >
      {children}
    </MapContext.Provider>
  );
}

export function useMapContext() {
  return useContext(MapContext);
}
