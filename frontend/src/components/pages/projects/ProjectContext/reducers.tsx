import { IForester } from '../Project';
import { GeoJSONFeature, MapLayer } from '../Project';
import { Flight, ProjectModule } from '../Project';
import { Project } from '../ProjectList';
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

function iforesterReducer(state: IForester[] | null, action: IForesterAction) {
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

function locationReducer(state: GeoJSONFeature | null, action: LocationAction) {
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

function flightsFilterSelectionReducer(
  state: string[],
  action: FlightsFilterSelectionAction
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

function mapLayersReducer(state: MapLayer[], action: MapLayersAction) {
  switch (action.type) {
    case 'set': {
      return action.payload ? action.payload : [];
    }
    case 'update': {
      if (action.payload) {
        if (state.length > 0) {
          return [...state, ...action.payload];
        } else {
          return action.payload;
        }
      } else {
        return state;
      }
    }
    case 'updateOne': {
      return state.map((layer) =>
        layer.layer_id === action.payload.layer_id ? action.payload : layer
      );
    }
    case 'remove': {
      if (action.payload) {
        if (state.length > 0 && action.payload.length === 1) {
          const layerIdToRemove: string | undefined =
            action.payload[0].layer_id;
          if (layerIdToRemove) {
            return state.filter((layer) => {
              if (layer.layer_id !== layerIdToRemove) {
                return layer;
              }
            });
          }
        }
      }
      return state;
    }
    case 'clear': {
      return [];
    }
    default: {
      return state;
    }
  }
}

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

function projectModulesReducer(
  state: ProjectModule[] | null,
  action: ProjectModulesAction
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

function projectRoleReducer(
  state: string | undefined,
  action: ProjectRoleAction
) {
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

export {
  iforesterReducer,
  locationReducer,
  flightsReducer,
  flightsFilterSelectionReducer,
  mapLayersReducer,
  projectFilterSelectionReducer,
  projectMembersReducer,
  projectModulesReducer,
  projectReducer,
  projectRoleReducer,
};
