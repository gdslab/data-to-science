import { createContext, Dispatch, useContext, useReducer } from 'react';

type IForesterControlState = {
  dbhMin: number;
  dbhMax: number;
  dbhVisibility: boolean;
  heightMin: number;
  heightMax: number;
  heightVisibility: boolean;
  speciesSelection: string[];
  speciesVisibility: boolean;
  visibleMarkers: string[];
  activeMarker: string;
  activeMarkerZoom: string;
};

type IForesterControlAction =
  | { type: 'SET_DBH_MIN'; payload: number }
  | { type: 'SET_DBH_MAX'; payload: number }
  | { type: 'SET_DBH_VISIBILITY'; payload: boolean }
  | { type: 'SET_HEIGHT_MIN'; payload: number }
  | { type: 'SET_HEIGHT_MAX'; payload: number }
  | { type: 'SET_HEIGHT_VISIBILITY'; payload: boolean }
  | { type: 'SET_SPECIES_SELECTION'; payload: string[] }
  | { type: 'SET_SPECIES_VISIBILITY'; payload: boolean }
  | { type: 'SET_VISIBLE_MARKERS'; payload: string[] }
  | { type: 'SET_ACTIVE_MARKER'; payload: string }
  | { type: 'SET_ACTIVE_MARKER_ZOOM'; payload: string };

const initialState = {
  dbhMin: -1,
  dbhMax: -1,
  dbhVisibility: true,
  heightMin: -1,
  heightMax: -1,
  heightVisibility: false,
  speciesSelection: [],
  speciesVisibility: false,
  visibleMarkers: [],
  activeMarker: '',
  activeMarkerZoom: '',
};

const IForesterControlContext = createContext<{
  state: IForesterControlState;
  dispatch: Dispatch<IForesterControlAction>;
}>({
  state: initialState,
  dispatch: () => null,
});

const reducer = (
  state: IForesterControlState,
  action: IForesterControlAction
): IForesterControlState => {
  switch (action.type) {
    case 'SET_DBH_MIN':
      return { ...state, dbhMin: action.payload };
    case 'SET_DBH_MAX':
      return { ...state, dbhMax: action.payload };
    case 'SET_DBH_VISIBILITY':
      return { ...state, dbhVisibility: action.payload };
    case 'SET_HEIGHT_MIN':
      return { ...state, heightMin: action.payload };
    case 'SET_HEIGHT_MAX':
      return { ...state, heightMax: action.payload };
    case 'SET_HEIGHT_VISIBILITY':
      return { ...state, heightVisibility: action.payload };
    case 'SET_SPECIES_SELECTION':
      return { ...state, speciesSelection: action.payload };
    case 'SET_SPECIES_VISIBILITY':
      return { ...state, speciesVisibility: action.payload };
    case 'SET_VISIBLE_MARKERS':
      return { ...state, visibleMarkers: action.payload };
    case 'SET_ACTIVE_MARKER':
      return { ...state, activeMarker: action.payload };
    case 'SET_ACTIVE_MARKER_ZOOM':
      return { ...state, activeMarkerZoom: action.payload };
    default:
      return state;
  }
};

const IForesterControlProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <IForesterControlContext.Provider value={{ state, dispatch }}>
      {children}
    </IForesterControlContext.Provider>
  );
};

export { IForesterControlProvider };
export function useIForesterControlContext() {
  return useContext(IForesterControlContext);
}
