import { GeoJSONFeature } from '../Project';
import { Flight } from '../Project';
import { Project } from '../ProjectList';
import { ProjectMember } from '../ProjectAccess';

import {
  LocationAction,
  FlightsAction,
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
  projectReducer,
  projectMembersReducer,
  projectRoleReducer,
};
