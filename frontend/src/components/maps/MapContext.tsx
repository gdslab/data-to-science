import axios from 'axios';
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useReducer,
} from 'react';
import { v4 as uuidv4 } from 'uuid';

import {
  DataProduct,
  Flight,
  MapLayerFeatureCollection,
  ProjectItem,
} from '../pages/workspace/projects/Project';
import {
  ActiveDataProductAction,
  ActiveMapToolAction,
  ActiveProjectAction,
  FlightsAction,
  GeoRasterIdAction,
  MapTool,
  ProjectsAction,
  ProjectsLoadedAction,
  ProjectFilterSelectionAction,
  ProjectsVisibleAction,
  SelectedTeamIdsAction,
  TileScaleAction,
} from './Maps';
import { areProjectsEqual } from './utils';

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
        const updatedDataProduct = {
          ...state,
          ...action.payload,
        } as DataProduct;
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

function activeProjectReducer(
  state: ProjectItem | null,
  action: ActiveProjectAction
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

type MapViewPropertiesState = {
  zoom: number;
} | null;
type MapViewPropertiesAction = {
  type: 'SET_VIEW_PROPERTIES';
  payload: MapViewPropertiesState;
};
function mapViewPropertiesReducer(
  state: MapViewPropertiesState,
  action: MapViewPropertiesAction
) {
  switch (action.type) {
    case 'SET_VIEW_PROPERTIES':
      return action.payload;
    default:
      return state;
  }
}

type ProjectLayersAction = {
  type: string;
  payload?: MapLayerFeatureCollection[];
};

function projectLayersReducer(
  state: MapLayerFeatureCollection[],
  action: ProjectLayersAction
) {
  switch (action.type) {
    case 'set': {
      return action.payload ? action.payload : [];
    }
    case 'clear': {
      return [];
    }
    default: {
      return state;
    }
  }
}

function projectsReducer(state: ProjectItem[] | null, action: ProjectsAction) {
  switch (action.type) {
    case 'set': {
      // Only update if projects are new or differ from current state
      if (
        !state ||
        !action.payload ||
        !areProjectsEqual(state, action.payload)
      ) {
        return action.payload;
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

function projectFilterSelectionReducer(
  state: string[],
  action: ProjectFilterSelectionAction
) {
  switch (action.type) {
    case 'set': {
      return action.payload ? action.payload : [];
    }
    case 'reset': {
      return [];
    }
    default: {
      return state;
    }
  }
}

function selectedTeamIdsReducer(
  state: string[],
  action: SelectedTeamIdsAction
) {
  switch (action.type) {
    case 'set': {
      return action.payload;
    }
    case 'reset': {
      return [];
    }
    default: {
      return state;
    }
  }
}

export type ProjectsLoadedState = 'initial' | 'loading' | 'loaded' | 'error';

function projectsLoadedReducer(
  state: ProjectsLoadedState,
  action: ProjectsLoadedAction
) {
  switch (action.type) {
    case 'set': {
      return action.payload;
    }
    default: {
      return state;
    }
  }
}

function projectsVisibleReducer(
  state: string[],
  action: ProjectsVisibleAction
) {
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
  activeProject: ProjectItem | null;
  activeProjectDispatch: React.Dispatch<ActiveProjectAction>;
  flights: Flight[];
  geoRasterId: string;
  geoRasterIdDispatch: React.Dispatch<GeoRasterIdAction>;
  mapViewProperties: MapViewPropertiesState;
  mapViewPropertiesDispatch: React.Dispatch<MapViewPropertiesAction>;
  projectLayers: MapLayerFeatureCollection[];
  projectLayersDispatch: React.Dispatch<ProjectLayersAction>;
  projects: ProjectItem[] | null;
  projectsDispatch: React.Dispatch<ProjectsAction>;
  projectsLoaded: ProjectsLoadedState;
  projectsLoadedDispatch: React.Dispatch<ProjectsLoadedAction>;
  projectFilterSelection: string[];
  projectFilterSelectionDispatch: React.Dispatch<ProjectFilterSelectionAction>;
  projectsVisible: string[];
  projectsVisibleDispatch: React.Dispatch<ProjectsVisibleAction>;
  selectedTeamIds: string[];
  selectedTeamIdsDispatch: React.Dispatch<SelectedTeamIdsAction>;
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
  mapViewProperties: null,
  mapViewPropertiesDispatch: () => {},
  projectLayers: [],
  projectLayersDispatch: () => {},
  projects: null,
  projectsDispatch: () => {},
  projectsLoaded: 'initial',
  projectsLoadedDispatch: () => {},
  projectFilterSelection: [],
  projectFilterSelectionDispatch: () => {},
  projectsVisible: [],
  projectsVisibleDispatch: () => {},
  selectedTeamIds: [],
  selectedTeamIdsDispatch: () => {},
  tileScale: 2,
  tileScaleDispatch: () => {},
};

const MapContext = createContext(context);

export function MapContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [activeDataProduct, activeDataProductDispatch] = useReducer(
    activeDataProductReducer,
    null
  );
  const [activeMapTool, activeMapToolDispatch] = useReducer(
    activeMapToolReducer,
    'map'
  );
  const [activeProject, activeProjectDispatch] = useReducer(
    activeProjectReducer,
    null
  );
  const [flights, flightsDispatch] = useReducer(flightsReducer, []);
  const [geoRasterId, geoRasterIdDispatch] = useReducer(geoRasterIdReducer, '');

  const [mapViewProperties, mapViewPropertiesDispatch] = useReducer(
    mapViewPropertiesReducer,
    null
  );
  const [projectLayers, projectLayersDispatch] = useReducer(
    projectLayersReducer,
    []
  );
  const [projects, projectsDispatch] = useReducer(projectsReducer, null);
  const [projectsLoaded, projectsLoadedDispatch] = useReducer(
    projectsLoadedReducer,
    'initial'
  );
  const [projectFilterSelection, projectFilterSelectionDispatch] = useReducer(
    projectFilterSelectionReducer,
    []
  );
  const [projectsVisible, projectsVisibleDispatch] = useReducer(
    projectsVisibleReducer,
    []
  );
  const [selectedTeamIds, selectedTeamIdsDispatch] = useReducer(
    selectedTeamIdsReducer,
    []
  );
  const [tileScale, tileScaleDispatch] = useReducer(tileScaleReducer, 2);

  async function getFlights(projectId) {
    try {
      const response = await axios.get(
        `${
          import.meta.env.VITE_API_V1_STR
        }/projects/${projectId}/flights?include_all=False`
      );
      if (response) {
        flightsDispatch({ type: 'set', payload: response.data });
      }
    } catch {
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
  }, [activeDataProduct, activeProject]);

  const contextValue = useMemo(
    () => ({
      activeDataProduct,
      activeDataProductDispatch,
      activeMapTool,
      activeMapToolDispatch,
      activeProject,
      activeProjectDispatch,
      flights,
      geoRasterId,
      geoRasterIdDispatch,

      mapViewProperties,
      mapViewPropertiesDispatch,
      projectFilterSelection,
      projectFilterSelectionDispatch,
      projectLayers,
      projectLayersDispatch,
      projects,
      projectsDispatch,
      projectsLoaded,
      projectsLoadedDispatch,
      projectsVisible,
      projectsVisibleDispatch,
      selectedTeamIds,
      selectedTeamIdsDispatch,
      tileScale,
      tileScaleDispatch,
    }),
    [
      activeDataProduct,
      activeMapTool,
      activeProject,
      flights,
      geoRasterId,
      mapViewProperties,
      projectFilterSelection,
      projectLayers,
      projects,
      projectsLoaded,
      projectsVisible,
      selectedTeamIds,
      tileScale,
    ]
  );

  return (
    <MapContext.Provider value={contextValue}>{children}</MapContext.Provider>
  );
}

export function useMapContext() {
  return useContext(MapContext);
}
