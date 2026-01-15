import { createContext, Dispatch, useContext, useReducer } from 'react';
import { DataProduct } from '../pages/workspace/projects/Project';

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
  background?: DataProduct;
  colorRamp: string;
}

export interface ColorBand extends ValueRange {
  idx: number;
}

export interface MultibandSymbology extends Symbology {
  red: ColorBand;
  green: ColorBand;
  blue: ColorBand;
}

type RasterState = {
  isLoaded: boolean;
  symbology: SingleBandSymbology | MultibandSymbology | null;
};

type State = Record<string, RasterState>;

type SymbologyAction = {
  type: 'SET_SYMBOLOGY';
  rasterId: string;
  payload: SingleBandSymbology | MultibandSymbology | null;
};

type ReadyStateAction = {
  type: 'SET_READY_STATE';
  rasterId: string;
  payload: boolean;
};

type RemoveRasterAction = {
  type: 'REMOVE_RASTER';
  rasterId: string;
};

type Action = SymbologyAction | ReadyStateAction | RemoveRasterAction;

const initialState: State = {};

const SymbologyContext = createContext<{
  state: State;
  dispatch: Dispatch<Action>;
}>({ state: initialState, dispatch: () => null });

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'SET_SYMBOLOGY':
      return {
        ...state,
        [action.rasterId]: {
          ...state[action.rasterId],
          symbology: action.payload,
        },
      };
    case 'SET_READY_STATE':
      return {
        ...state,
        [action.rasterId]: {
          ...state[action.rasterId],
          isLoaded: action.payload,
        },
      };
    case 'REMOVE_RASTER': {
      const { [action.rasterId]: _, ...remainingState } = state;
      return remainingState;
    }
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
