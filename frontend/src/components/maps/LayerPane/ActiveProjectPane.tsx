import { useMemo } from 'react';

import FlightCard from './FlightCard';
import { useMapContext } from '../MapContext';
import MapToolbar from '../MapToolbar';
import { Project } from '../../pages/workspace/projects/ProjectList';

import { sortedFlightsByDateAndId } from './utils';

type ActiveProjectPaneProps = { project: Project };

export default function ActiveProjectPane({ project }: ActiveProjectPaneProps) {
  const { flights } = useMapContext();

  // Sort flights by date, followed by id if the dates are a match
  const sortedFlights = useMemo(() => {
    const flightList = flights ?? [];
    return sortedFlightsByDateAndId(flightList);
  }, [flights]);

  return (
    <article className="h-[calc(100%_-_44px)] p-4">
      <header className="h-44">
        <h1 className="truncate" title={project.title}>
          {project.title}
        </h1>
        <p className="text-slate-700 text-sm font-light line-clamp-2">
          {project.description}
        </p>
        <MapToolbar />
      </header>
      <ul className="h-[calc(100%_-_160px)] space-y-2 overflow-y-auto pb-16">
        {sortedFlights.map((flight) => (
          <li key={flight.id}>
            <FlightCard flight={flight} />
          </li>
        ))}
      </ul>
    </article>
  );
}
