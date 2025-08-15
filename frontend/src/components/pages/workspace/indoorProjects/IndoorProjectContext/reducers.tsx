import { ProjectMember } from '../../projects/ProjectAccess';

import { IndoorProjectAction } from './actions';

/**
 * State interface for the Indoor Project context
 */
export type IndoorProjectState = {
  projectMembers: ProjectMember[] | null;
  selectedDAP: number | null; // DAP: Days after planting
};

const initialState: IndoorProjectState = {
  projectMembers: null,
  selectedDAP: null,
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
    default:
      return state;
  }
}

export { initialState };
