import axios, { AxiosResponse } from 'axios';
import { createContext, useContext, useEffect, useReducer } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { FlightAction } from './actions';
import { flightReducer } from './reducers';

import { Flight } from '../Project';

interface Context {
  flight: Flight | null;
  flightDispatch: React.Dispatch<FlightAction>;
}

const context: Context = {
  flight: null,
  flightDispatch: () => {},
};

const FlightContext = createContext(context);

interface FlightContextProvider {
  children: React.ReactNode;
}

export function FlightContextProvider({ children }: FlightContextProvider) {
  const [flight, flightDispatch] = useReducer(flightReducer, null);

  const navigate = useNavigate();
  const params = useParams();

  // fetch flight when the flightID in the request changes
  useEffect(() => {
    async function getFlight() {
      try {
        const response: AxiosResponse<Flight> = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/flights/${
            params.flightId
          }`
        );
        if (response) {
          flightDispatch({ type: 'set', payload: response.data });
        } else {
          flightDispatch({ type: 'clear', payload: null });
        }
      } catch (err) {
        if (axios.isAxiosError(err)) {
          console.error(err.response?.data.detail);
        } else {
          console.error(err);
        }
        flightDispatch({ type: 'clear', payload: null });
        // no flights found or unexpected error, return to project page
        navigate(`/projects/${params.projectId}`);
      }
    }
    if (params.projectId && params.flightId) {
      getFlight();
    } else {
      flightDispatch({ type: 'clear', payload: null });
    }
  }, [params.flightId]);

  return (
    <FlightContext.Provider
      value={{
        flight,
        flightDispatch,
      }}
    >
      {children}
    </FlightContext.Provider>
  );
}

export function useFlightContext() {
  return useContext(FlightContext);
}
