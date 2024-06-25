import { MapLayerFeatureCollection } from '../Project';
import { GeoJSONFeature } from '../Project';
import { Flight } from '../Project';
import { Project } from '../ProjectList';
import { ProjectMember } from '../ProjectAccess';

import {
  LocationAction,
  FlightsAction,
  FlightsFilterSelectionAction,
  MapLayersAction,
  ProjectAction,
  ProjectMembersAction,
  ProjectRoleAction,
} from './actions';

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

function mapLayersReducer(state: MapLayerFeatureCollection[], action: MapLayersAction) {
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
    case 'remove': {
      if (action.payload) {
        if (state.length > 0 && action.payload.length === 1) {
          const layerIdToRemove: string | undefined =
            action.payload[0].features[0].properties?.layer_id;
          if (layerIdToRemove) {
            return state.filter((fc) => {
              if (fc && fc.features && fc.features.length > 0) {
                if (
                  fc.features[0].properties &&
                  'layer_id' in fc.features[0].properties
                ) {
                  if (fc.features[0].properties.layer_id !== layerIdToRemove) {
                    return fc;
                  }
                }
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

export {
  locationReducer,
  flightsReducer,
  flightsFilterSelectionReducer,
  mapLayersReducer,
  projectReducer,
  projectMembersReducer,
  projectRoleReducer,
};
