import { Link, useParams } from 'react-router-dom';

import { useProjectContext } from '../ProjectContext';
import UASIcon from '../../../../assets/uas-icon.svg';
import HintText from '../../../HintText';
import { classNames, sorter } from '../../../utils';

export default function FlightDataNav() {
  const { flightId, projectId } = useParams();
  const { flights, flightsFilterSelection } = useProjectContext();

  if (flights && flights.length > 0) {
    return (
      <nav className="grow flex flex-col min-h-0 items-center gap-4 p-4 min-w-48 overflow-y-auto">
        {flights
          .filter(({ sensor }) => flightsFilterSelection.indexOf(sensor) > -1)
          .sort((a, b) =>
            sorter(new Date(a.acquisition_date), new Date(b.acquisition_date), 'desc')
          )
          .map((flight) => (
            <Link
              key={flight.id}
              className={classNames(
                flight.id === flightId
                  ? 'border-accent2 border-4'
                  : 'border-slate-400 border-2',
                'flex flex-col items-center justify-center h-36 min-h-36 w-36 bg-white hover:border-accent2 rounded-md'
              )}
              to={`/projects/${projectId}/flights/${flight.id}/data`}
            >
              <img className="w-8" src={UASIcon} />
              <span className="block text-lg">{flight.sensor}</span>
              {flight.acquisition_date}
              <HintText>{flight.platform}</HintText>
            </Link>
          ))}
      </nav>
    );
  } else {
    return null;
  }
}
