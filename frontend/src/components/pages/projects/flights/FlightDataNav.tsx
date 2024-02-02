import axios from 'axios';
import { useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useProjectContext } from '../ProjectContext';
import UASIcon from '../../../../assets/uas-icon.svg';
import HintText from '../../../HintText';
import { sorter } from '../../../utils';

export default function FlightDataNav() {
  const { projectId } = useParams();
  const { flights, flightsDispatch } = useProjectContext();

  async function fetchFlights() {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/flights`
      );
      if (response) flightsDispatch({ type: 'set', payload: response.data });
    } catch (err) {
      flightsDispatch({ type: 'clear', payload: null });
    }
  }

  useEffect(() => {
    if (!flights) {
      fetchFlights();
    }
  }, [flights]);

  if (flights && flights.length > 0) {
    return (
      <nav className="grow flex flex-col min-h-0 items-center gap-4 p-4 min-w-48 overflow-y-auto">
        {flights
          .sort((a, b) =>
            sorter(new Date(a.acquisition_date), new Date(b.acquisition_date), 'desc')
          )
          .map((flight) =>
            flight.data_products.length > 0 ? (
              <Link
                key={flight.id}
                className="flex flex-col items-center justify-center h-36 min-h-36 w-36 bg-white border-2 border-slate-400 hover:border-slate-700 rounded-md"
                to={`/projects/${projectId}/flights/${flight.id}/data`}
              >
                <img className="w-8" src={UASIcon} />
                <span className="block text-lg">{flight.sensor}</span>
                {flight.acquisition_date}
                <HintText>{flight.platform}</HintText>
              </Link>
            ) : null
          )}
      </nav>
    );
  } else {
    return null;
  }
}
