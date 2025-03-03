import { useEffect, useMemo, useRef } from "react";
import { Link, useParams } from "react-router-dom";

import { useProjectContext } from "../ProjectContext";
import { classNames, sorter } from "../../../utils";

import UASIcon from "../../../../assets/uas-icon.svg";

export default function FlightDataNav() {
  const { flightId, projectId } = useParams();
  const { flights, flightsFilterSelection } = useProjectContext();
  const selectedFlightRef = useRef<HTMLAnchorElement | null>(null);

  const filteredAndSortedFlights = useMemo(
    () =>
      flights
        ? flights
            .filter(({ sensor }) => flightsFilterSelection.indexOf(sensor) > -1)
            .sort((a, b) =>
              sorter(
                new Date(a.acquisition_date),
                new Date(b.acquisition_date),
                "desc"
              )
            )
        : [],
    [flights, flightsFilterSelection]
  );

  useEffect(() => {
    if (selectedFlightRef.current) {
      selectedFlightRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [flightId]);

  if (!flights || flights.length === 0) {
    return null;
  }

  return (
    <nav className="grow flex flex-col min-h-0 items-center gap-4 p-4 min-w-48 overflow-y-auto">
      {filteredAndSortedFlights.map((flight) => (
        <Link
          key={flight.id}
          ref={flight.id === flightId ? selectedFlightRef : null}
          className={classNames(
            flight.id === flightId
              ? "border-accent2 border-4"
              : "border-slate-400 border-2",
            "flex flex-col items-center justify-center h-36 min-h-36 w-36 bg-white hover:border-accent2 rounded-md p-1"
          )}
          to={`/projects/${projectId}/flights/${flight.id}/data`}
        >
          <img className="w-8" src={UASIcon} />
          <span className="block text-lg">{flight.sensor}</span>
          {flight.acquisition_date}
          <span className="w-full text-center text-slate-700 text-sm font-light truncate">
            {flight.name ? flight.name : ""}
          </span>
          <span className="w-full text-center text-slate-700 text-sm font-light truncate">
            {flight.platform}
          </span>
        </Link>
      ))}
    </nav>
  );
}
