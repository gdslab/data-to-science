import {
  createContext,
  Dispatch,
  useContext,
  useReducer,
  ReactNode,
} from 'react';
import { Outlet } from 'react-router-dom';

/**
 * State interface for the Indoor Project context
 */
type IndoorProjectState = {
  selectedDAP: number | null; // DAP: Days after planting
};

/**
 * Action types for the Indoor Project context
 */
type IndoorProjectAction = {
  type: 'SET_SELECTED_DAP';
  payload: number | null;
};

const initialState: IndoorProjectState = {
  selectedDAP: null,
};

/**
 * Context interface for Indoor Project
 */
interface IndoorProjectContextType {
  state: IndoorProjectState;
  dispatch: Dispatch<IndoorProjectAction>;
}

const IndoorProjectContext = createContext<
  IndoorProjectContextType | undefined
>(undefined);
IndoorProjectContext.displayName = 'IndoorProjectContext';

const reducer = (
  state: IndoorProjectState,
  action: IndoorProjectAction
): IndoorProjectState => {
  switch (action.type) {
    case 'SET_SELECTED_DAP':
      return { ...state, selectedDAP: action.payload };
    default:
      return state;
  }
};

interface IndoorProjectProviderProps {
  children?: ReactNode;
}

/**
 * Provider component for Indoor Project context
 */
const IndoorProjectProvider = ({ children }: IndoorProjectProviderProps) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <IndoorProjectContext.Provider value={{ state, dispatch }}>
      {children ?? <Outlet />}
    </IndoorProjectContext.Provider>
  );
};

export { IndoorProjectProvider };

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
