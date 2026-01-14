import { ProjectMember } from '../../projects/ProjectAccess';
import { IndoorProjectAPIResponse } from '../IndoorProject.d';

import { IndoorProjectAction } from './actions';

/**
 * State interface for the Indoor Project context
 */
export type IndoorProjectState = {
  indoorProject: IndoorProjectAPIResponse | null;
  projectMembers: ProjectMember[] | null;
  selectedDAP: number | null; // DAP: Days after planting
  projectRole: string | undefined;
};

const initialState: IndoorProjectState = {
  indoorProject: null,
  projectMembers: null,
  selectedDAP: null,
  projectRole: undefined,
};

export function indoorProjectReducer(
  state: IndoorProjectState,
  action: IndoorProjectAction
): IndoorProjectState {
  switch (action.type) {
    case 'SET_SELECTED_DAP':
      return { ...state, selectedDAP: action.payload };
    case 'SET_PROJECT_MEMBERS':
      return { ...state, projectMembers: action.payload };
    case 'CLEAR_PROJECT_MEMBERS':
      return { ...state, projectMembers: null };
    case 'SET_PROJECT_ROLE':
      return { ...state, projectRole: action.payload };
    case 'CLEAR_PROJECT_ROLE':
      return { ...state, projectRole: undefined };
    case 'SET_INDOOR_PROJECT':
      return { ...state, indoorProject: action.payload };
    case 'CLEAR_INDOOR_PROJECT':
      return { ...state, indoorProject: null };
    default:
      return state;
  }
}

export { initialState };
