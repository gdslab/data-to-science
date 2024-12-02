import { createContext, Dispatch, useContext, useReducer } from 'react';

export type SymbologyMode = 'meanStdDev' | 'minMax' | 'userDefined';

export type Symbology = {
  meanStdDev: number;
  mode: SymbologyMode;
  opacity: number;
};

type ValueRange = {
  min: number;
  max: number;
  userMin: number;
  userMax: number;
};

export interface SingleBandSymbology extends Symbology, ValueRange {
  colorRamp: string;
}

export interface ColorBand extends ValueRange {
  idx: number;
}

export interface MultiBandSymbology extends Symbology {
  red: ColorBand;
  green: ColorBand;
  blue: ColorBand;
}

type State = {
  isLoaded: boolean;
  symbology: SingleBandSymbology | MultiBandSymbology | null;
};

type Action =
  | { type: 'SET_SYMBOLOGY'; payload: SingleBandSymbology | MultiBandSymbology | null }
  | { type: 'SET_READY_STATE'; payload: boolean };

const initialState = {
  isLoaded: false,
  symbology: null,
};

const SymbologyContext = createContext<{
  state: State;
  dispatch: Dispatch<Action>;
}>({ state: initialState, dispatch: () => null });

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'SET_SYMBOLOGY':
      return { ...state, symbology: action.payload };
    case 'SET_READY_STATE':
      return { ...state, isLoaded: action.payload };
    default:
      return state;
  }
};

const SymbologyProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <SymbologyContext.Provider value={{ state, dispatch }}>
      {children}
    </SymbologyContext.Provider>
  );
};

export { SymbologyProvider as RasterSymbologyProvider };
export function useRasterSymbologyContext() {
  return useContext(SymbologyContext);
}
