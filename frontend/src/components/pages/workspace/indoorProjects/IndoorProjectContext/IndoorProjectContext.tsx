import { AxiosResponse, isAxiosError } from 'axios';
import {
  createContext,
  Dispatch,
  ReactNode,
  useContext,
  useEffect,
  useReducer,
} from 'react';
import { Outlet, useParams } from 'react-router-dom';

import api from '../../../../../api';

import { IndoorProjectAction } from './actions';
import {
  IndoorProjectState,
  indoorProjectReducer,
  initialState,
} from './reducers';

/**
 * Context interface for Indoor Project
 */
interface IndoorProjectContextType {
  state: IndoorProjectState;
  dispatch: Dispatch<IndoorProjectAction>;
}

export async function getProjectMembers(
  indoorProjectId: string,
  dispatch: React.Dispatch<IndoorProjectAction>
) {
  try {
    const response: AxiosResponse<any[]> = await api.get(
      `/indoor_projects/${indoorProjectId}/members`
    );
    if (response) {
      dispatch({ type: 'SET_PROJECT_MEMBERS', payload: response.data });
    } else {
      dispatch({ type: 'CLEAR_PROJECT_MEMBERS', payload: null });
    }
  } catch (err) {
    if (isAxiosError(err)) {
      console.log(err.response?.data);
    } else {
      console.error(err);
    }
    dispatch({ type: 'CLEAR_PROJECT_MEMBERS', payload: null });
  }
}

const IndoorProjectContext = createContext<
  IndoorProjectContextType | undefined
>(undefined);
IndoorProjectContext.displayName = 'IndoorProjectContext';

interface IndoorProjectProviderProps {
  children?: ReactNode;
}

/**
 * Provider component for Indoor Project context
 */
export const IndoorProjectProvider = ({
  children,
}: IndoorProjectProviderProps) => {
  const [state, dispatch] = useReducer(indoorProjectReducer, initialState);
  const params = useParams();

  useEffect(() => {
    if (params.indoorProjectId) {
      getProjectMembers(params.indoorProjectId, dispatch);
    } else {
      dispatch({ type: 'CLEAR_PROJECT_MEMBERS', payload: null });
    }
  }, [params.indoorProjectId]);

  return (
    <IndoorProjectContext.Provider value={{ state, dispatch }}>
      {children ?? <Outlet />}
    </IndoorProjectContext.Provider>
  );
};

/**
 * Custom hook to use the Indoor Project context
 * @throws {Error} If used outside of IndoorProjectProvider
 */
export function useIndoorProjectContext(): IndoorProjectContextType {
  const context = useContext(IndoorProjectContext);
  if (context === undefined) {
    throw new Error(
      'useIndoorProjectContext must be used within an IndoorProjectProvider'
    );
  }
  return context;
}
