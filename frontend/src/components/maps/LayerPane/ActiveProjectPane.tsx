import { useMemo, useEffect, useRef } from 'react';

import FlightCard from './FlightCard';
import { useMapContext } from '../MapContext';
import MapToolbar from '../MapToolbar';
import { Project } from '../../pages/workspace/projects/ProjectList';

import { sortedFlightsByDateAndId } from './utils';

type ActiveProjectPaneProps = { project: Project };

export default function ActiveProjectPane({ project }: ActiveProjectPaneProps) {
  const { flights, activeDataProduct } = useMapContext();
  const scrollContainerRef = useRef<HTMLUListElement | null>(null);

  // Sort flights by date, followed by id if the dates are a match
  const sortedFlights = useMemo(() => {
    const flightList = flights ?? [];
    return sortedFlightsByDateAndId(flightList);
  }, [flights]);

  // Function to attempt scrolling to active data product
  const scrollToActiveDataProduct = (delay = 100) => {
    if (activeDataProduct && scrollContainerRef.current) {
      const scrollToElement = () => {
        if (scrollContainerRef.current) {
          const activeCard = scrollContainerRef.current.querySelector(
            `[data-product-id="${activeDataProduct.id}"]`
          );
          if (activeCard) {
            activeCard.scrollIntoView({
              behavior: 'smooth',
              block: 'start',
            });
            return true; // Successfully found and scrolled
          } else {
            return false; // Not found
          }
        }
        return false;
      };

      // Try immediately with requestAnimationFrame
      requestAnimationFrame(() => {
        if (!scrollToElement()) {
          // If not found immediately, try again with delay
          const timeoutId = setTimeout(scrollToElement, delay);
          return () => clearTimeout(timeoutId);
        }
      });
    }
  };

  // Handle changes to activeDataProduct (when clicking within LayerPane)
  useEffect(() => {
    scrollToActiveDataProduct(100);
  }, [activeDataProduct]);

  // Handle initial mount and when flights load (when navigating from View button)
  useEffect(() => {
    if (
      activeDataProduct &&
      flights &&
      flights.length > 0 &&
      scrollContainerRef.current
    ) {
      // Give more time for DOM to render when coming from navigation
      scrollToActiveDataProduct(300);
    }
  }, [flights, activeDataProduct]);

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
      <ul
        ref={scrollContainerRef}
        className="h-[calc(100%_-_160px)] space-y-2 overflow-y-auto pb-16"
      >
        {sortedFlights.map((flight) => (
          <li key={flight.id}>
            <FlightCard flight={flight} />
          </li>
        ))}
      </ul>
    </article>
  );
}
