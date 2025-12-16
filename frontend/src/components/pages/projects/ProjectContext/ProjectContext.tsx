import { AxiosResponse, isAxiosError } from 'axios';
import { createContext, useContext, useEffect, useReducer } from 'react';
import { useParams } from 'react-router';

import {
  Flight,
  GeoJSONFeature,
  IForester,
  MapLayer,
  ProjectDetail,
  ProjectModule,
} from '../Project';
import { ProjectMember } from '../ProjectAccess';

import {
  IForesterAction,
  LocationAction,
  FlightsAction,
  FlightsFilterSelectionAction,
  MapLayersAction,
  ProjectAction,
  ProjectFilterSelectionAction,
  ProjectMembersAction,
  ProjectModulesAction,
  ProjectRoleAction,
} from './actions';
import {
  iforesterReducer,
  locationReducer,
  flightsReducer,
  flightsFilterSelectionReducer,
  mapLayersReducer,
  projectReducer,
  projectMembersReducer,
  projectModulesReducer,
  projectRoleReducer,
  projectFilterSelectionReducer,
} from './reducers';

import api from '../../../../api';

interface Context {
  iforester: IForester[] | null;
  iforesterDispatch: React.Dispatch<IForesterAction>;
  location: GeoJSONFeature | null;
  locationDispatch: React.Dispatch<LocationAction>;
  mapLayers: MapLayer[];
  mapLayersDispatch: React.Dispatch<MapLayersAction>;
  project: ProjectDetail | null;
  projectDispatch: React.Dispatch<ProjectAction>;
  projectMembers: ProjectMember[] | null;
  projectMembersDispatch: React.Dispatch<ProjectMembersAction>;
  projectModules: ProjectModule[] | null;
  projectModulesDispatch: React.Dispatch<ProjectModulesAction>;
  projectRole: string | undefined;
  projectRoleDispatch: React.Dispatch<ProjectRoleAction>;
  projectFilterSelection: string[];
  projectFilterSelectionDispatch: React.Dispatch<ProjectFilterSelectionAction>;
  flights: Flight[] | null;
  flightsDispatch: React.Dispatch<FlightsAction>;
  flightsFilterSelection: string[];
  flightsFilterSelectionDispatch: React.Dispatch<FlightsFilterSelectionAction>;
}

const context: Context = {
  iforester: null,
  iforesterDispatch: () => {},
  location: null,
  locationDispatch: () => {},
  mapLayers: [],
  mapLayersDispatch: () => {},
  project: null,
  projectDispatch: () => {},
  projectMembers: null,
  projectMembersDispatch: () => {},
  projectModules: null,
  projectModulesDispatch: () => {},
  projectRole: undefined,
  projectRoleDispatch: () => {},
  projectFilterSelection: [],
  projectFilterSelectionDispatch: () => {},
  flights: null,
  flightsDispatch: () => {},
  flightsFilterSelection: [],
  flightsFilterSelectionDispatch: () => {},
};

export async function getProjectMembers(
  projectId: string,
  projectMembersDispatch: React.Dispatch<ProjectMembersAction>
) {
  try {
    const response: AxiosResponse<ProjectMember[]> = await api.get(
      `/projects/${projectId}/members`
    );
    if (response) {
      projectMembersDispatch({ type: 'set', payload: response.data });
    } else {
      projectMembersDispatch({ type: 'clear', payload: null });
    }
  } catch (err) {
    if (isAxiosError(err)) {
      console.log(err.response?.data);
    } else {
      console.error(err);
    }
    projectMembersDispatch({ type: 'clear', payload: null });
  }
}

export async function getProjectModules(
  projectId: string,
  projectModulesDispatch: React.Dispatch<ProjectModulesAction>
) {
  try {
    const response: AxiosResponse<ProjectModule[]> = await api.get(
      `/projects/${projectId}/modules`
    );
    if (response) {
      projectModulesDispatch({ type: 'set', payload: response.data });
    } else {
      projectModulesDispatch({ type: 'clear', payload: null });
    }
  } catch (err) {
    if (isAxiosError(err)) {
      console.log(err.response?.data);
    } else {
      console.error(err);
    }
    projectModulesDispatch({ type: 'clear', payload: null });
  }
}

export async function getMapLayers(
  projectId: string,
  mapLayersDispatch: React.Dispatch<MapLayersAction>
) {
  try {
    const response: AxiosResponse<MapLayer[]> = await api.get(
      `/projects/${projectId}/vector_layers`
    );
    if (response.status === 200) {
      mapLayersDispatch({ type: 'set', payload: response.data });
    } else {
      mapLayersDispatch({ type: 'clear' });
    }
  } catch (err) {
    if (isAxiosError(err)) {
      console.log(err.response?.data);
    } else {
      console.error(err);
    }
    mapLayersDispatch({ type: 'clear' });
  }
}

const ProjectContext = createContext(context);

interface ProjectContextProvider {
  children: React.ReactNode;
}

export function ProjectContextProvider({ children }: ProjectContextProvider) {
  const [iforester, iforesterDispatch] = useReducer(iforesterReducer, null);
  const [location, locationDispatch] = useReducer(locationReducer, null);
  const [flights, flightsDispatch] = useReducer(flightsReducer, null);
  const [flightsFilterSelection, flightsFilterSelectionDispatch] = useReducer(
    flightsFilterSelectionReducer,
    []
  );
  const [projectFilterSelection, projectFilterSelectionDispatch] = useReducer(
    projectFilterSelectionReducer,
    []
  );
  const [mapLayers, mapLayersDispatch] = useReducer(mapLayersReducer, []);
  const [project, projectDispatch] = useReducer(projectReducer, null);
  const [projectMembers, projectMembersDispatch] = useReducer(
    projectMembersReducer,
    null
  );
  const [projectModules, projectModulesDispatch] = useReducer(
    projectModulesReducer,
    null
  );
  const [projectRole, projectRoleDispatch] = useReducer(
    projectRoleReducer,
    undefined
  );

  const params = useParams();

  useEffect(() => {
    async function getLocation(project: ProjectDetail) {
      try {
        const response: AxiosResponse<GeoJSONFeature> = await api.get(
          `/locations/${project.id}/${project.location_id}`
        );
        if (response) {
          locationDispatch({ type: 'set', payload: response.data });
        } else {
          locationDispatch({ type: 'clear', payload: null });
        }
      } catch (err) {
        if (isAxiosError(err)) {
          console.log(err.response?.data);
        } else {
          console.error(err);
        }
        locationDispatch({ type: 'clear', payload: null });
      }
    }

    if (project) {
      getLocation(project);
    } else {
      locationDispatch({ type: 'clear', payload: null });
    }
  }, [project]);

  useEffect(() => {
    if (params.projectId) {
      getMapLayers(params.projectId, mapLayersDispatch);
    } else {
      mapLayersDispatch({ type: 'clear' });
    }
  }, [params.projectId]);

  useEffect(() => {
    if (params.projectId) {
      getProjectMembers(params.projectId, projectMembersDispatch);
    } else {
      projectMembersDispatch({ type: 'clear', payload: null });
    }
  }, [params.projectId]);

  return (
    <ProjectContext.Provider
      value={{
        iforester,
        iforesterDispatch,
        flights,
        flightsDispatch,
        flightsFilterSelection,
        flightsFilterSelectionDispatch,
        location,
        locationDispatch,
        mapLayers,
        mapLayersDispatch,
        project,
        projectDispatch,
        projectMembers,
        projectMembersDispatch,
        projectModules,
        projectModulesDispatch,
        projectRole,
        projectRoleDispatch,
        projectFilterSelection,
        projectFilterSelectionDispatch,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProjectContext() {
  return useContext(ProjectContext);
}
