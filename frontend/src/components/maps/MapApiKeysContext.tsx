import { createContext, useContext, useReducer } from 'react';

export type MapboxAccessTokenAction = {
  type: 'set';
  payload: string;
};

export type MaptilerApiKeyAction = {
  type: 'set';
  payload: string;
};

function mapboxAccessTokenReducer(
  state: string,
  action: MapboxAccessTokenAction
) {
  switch (action.type) {
    case 'set': {
      return action.payload;
    }
    default:
      return state;
  }
}

function maptilerApiKeyReducer(state: string, action: MaptilerApiKeyAction) {
  switch (action.type) {
    case 'set': {
      return action.payload;
    }
    default:
      return state;
  }
}

type MapApiKeysContextType = {
  mapboxAccessToken: string;
  mapboxAccessTokenDispatch: React.Dispatch<MapboxAccessTokenAction>;
  maptilerApiKey: string;
  maptilerApiKeyDispatch: React.Dispatch<MaptilerApiKeyAction>;
};

const MapApiKeysContext = createContext<MapApiKeysContextType>({
  mapboxAccessToken: '',
  mapboxAccessTokenDispatch: () => {},
  maptilerApiKey: '',
  maptilerApiKeyDispatch: () => {},
});

export function MapApiKeysContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  console.log('-----MapApiKeysContext.tsx rendered-----');
  const [mapboxAccessToken, mapboxAccessTokenDispatch] = useReducer(
    mapboxAccessTokenReducer,
    ''
  );
  const [maptilerApiKey, maptilerApiKeyDispatch] = useReducer(
    maptilerApiKeyReducer,
    ''
  );

  return (
    <MapApiKeysContext.Provider
      value={{
        mapboxAccessToken,
        mapboxAccessTokenDispatch,
        maptilerApiKey,
        maptilerApiKeyDispatch,
      }}
    >
      {children}
    </MapApiKeysContext.Provider>
  );
}

export function useMapApiKeys() {
  return useContext(MapApiKeysContext);
}
