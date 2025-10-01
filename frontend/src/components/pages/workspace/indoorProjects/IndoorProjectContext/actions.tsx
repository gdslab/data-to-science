import { ProjectMember } from '../../projects/ProjectAccess';
import { IndoorProjectAPIResponse } from '../IndoorProject.d';

export type IndoorProjectAction =
  | {
      type: 'SET_SELECTED_DAP';
      payload: number | null;
    }
  | {
      type: 'SET_PROJECT_MEMBERS';
      payload: ProjectMember[] | null;
    }
  | {
      type: 'CLEAR_PROJECT_MEMBERS';
      payload: null;
    }
  | {
      type: 'SET_PROJECT_ROLE';
      payload: string | undefined;
    }
  | {
      type: 'CLEAR_PROJECT_ROLE';
      payload: undefined;
    }
  | {
      type: 'SET_INDOOR_PROJECT';
      payload: IndoorProjectAPIResponse | null;
    }
  | {
      type: 'CLEAR_INDOOR_PROJECT';
      payload: null;
    };
