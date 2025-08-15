import { ProjectMember } from '../../projects/ProjectAccess';

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
    };
