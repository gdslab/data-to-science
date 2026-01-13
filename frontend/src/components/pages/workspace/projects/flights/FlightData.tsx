import { useEffect, useRef } from 'react';
import { Params, useLoaderData } from 'react-router';

import FlightDataNav from './FlightDataNav';
import { useProjectContext } from '../ProjectContext';
import { DataProduct, Flight } from '../Project';
import FlightDataTabNav from './FlightDataTabNav';

import { RawDataProps } from './RawData/RawData.types';
import { User } from '../../../../../AuthContext';

import api from '../../../../../api';

export async function loader({ params }: { params: Params<string> }) {
  const profile = localStorage.getItem('userProfile');
  const user: User | null = profile ? JSON.parse(profile) : null;
  if (!user) return { dataProducts: [], rawData: [], flights: [], role: null };

  try {
    const dataProducts = await api.get(
      `/projects/${params.projectId}/flights/${params.flightId}/data_products`
    );
    const rawData = await api.get(
      `/projects/${params.projectId}/flights/${params.flightId}/raw_data`
    );
    const flights = await api.get(`/projects/${params.projectId}/flights`);
    const project_member = await api.get(
      `/projects/${params.projectId}/members/${user.id}`
    );
    if (dataProducts && rawData && flights && project_member) {
      return {
        dataProducts: dataProducts.data,
        rawData: rawData.data,
        flights: flights.data,
        role: project_member.data.role,
      };
    } else {
      return { dataProducts: [], rawData: [], flights: [], role: null };
    }
  } catch {
    console.error('Unable to retrieve raw data and data products');
    return { dataProducts: [], rawData: [], flights: [], role: null };
  }
}

export type FlightData = {
  dataProducts: DataProduct[];
  rawData: RawDataProps[];
  flights: Flight[];
  role: string | null;
};

export default function FlightData() {
  const { dataProducts, rawData, flights, role } =
    useLoaderData() as FlightData;
  const {
    flights: contextFlights,
    flightsDispatch,
    flightsFilterSelection,
    flightsFilterSelectionDispatch,
    projectRoleDispatch,
  } = useProjectContext();

  const flightsLoaderRef = useRef<Flight[] | null>(null);

  useEffect(() => {
    if (role) projectRoleDispatch({ type: 'set', payload: role });
  }, [projectRoleDispatch, role]);

  useEffect(() => {
    // Only update if flights data actually changed (not just reference)
    if (flights && flightsLoaderRef.current !== flights) {
      flightsLoaderRef.current = flights;
      flightsDispatch({ type: 'set', payload: flights });

      // Initialize filter selection if not already set
      if (contextFlights) {
        // no previous flights, so select any sensor in flights
        if (contextFlights.length === 0) {
          flightsFilterSelectionDispatch({
            type: 'set',
            payload: [...new Set(flights.map(({ sensor }) => sensor))],
          });
        } else {
          // compare previous sensors with sensor in new flights
          const prevSensors = contextFlights.map(({ sensor }) => sensor);
          const newSensors = flights
            .filter(
              ({ sensor }) =>
                prevSensors.indexOf(sensor) < 0 &&
                flightsFilterSelection.indexOf(sensor) < 0
            )
            .map(({ sensor }) => sensor);
          // if any new sensors were found, add to filter selection options and check
          if (newSensors.length > 0) {
            flightsFilterSelectionDispatch({
              type: 'set',
              payload: [...flightsFilterSelection, ...newSensors],
            });
          }
        }
      } else {
        flightsFilterSelectionDispatch({
          type: 'set',
          payload: [...new Set(flights.map(({ sensor }) => sensor))],
        });
      }
    }
  }, [
    flights,
    flightsDispatch,
    flightsFilterSelection,
    flightsFilterSelectionDispatch,
    contextFlights,
  ]);

  return (
    <div className="flex flex-row h-full">
      {contextFlights && contextFlights.length > 0 ? <FlightDataNav /> : null}
      <div className="flex flex-col h-full w-full gap-4 p-4">
        <div className="grow min-h-0">
          <FlightDataTabNav dataProducts={dataProducts} rawData={rawData} />
        </div>
      </div>
    </div>
  );
}
