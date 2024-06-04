import { FeatureCollection } from 'geojson';

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

function mapLayersReducer(state: FeatureCollection[], action: MapLayersAction) {
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
