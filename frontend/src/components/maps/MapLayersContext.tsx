import { createContext, Dispatch, useContext, useReducer } from 'react';

export type MapLayerProps = {
  id: string;
  name: string;
  checked: boolean;
  color: string;
  opacity: number;
  type: string;
  signedUrl: string;
};

type MapLayerState = {
  layers: MapLayerProps[];
};

type MapLayerAction = {
  type: 'SET_LAYERS';
  payload: MapLayerProps[];
};

const initialState = {
  layers: [],
};

const MapLayerContext = createContext<{
  state: MapLayerState;
  dispatch: Dispatch<MapLayerAction>;
}>({ state: initialState, dispatch: () => null });

const reducer = (state: MapLayerState, action: MapLayerAction): MapLayerState => {
  switch (action.type) {
    case 'SET_LAYERS':
      return { ...state, layers: action.payload };
    default:
      return state;
  }
};

const MapLayerProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <MapLayerContext.Provider value={{ state, dispatch }}>
      {children}
    </MapLayerContext.Provider>
  );
};

export { MapLayerProvider };
export function useMapLayerContext() {
  return useContext(MapLayerContext);
}
