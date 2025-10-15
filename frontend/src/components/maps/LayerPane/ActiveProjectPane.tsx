import { useMemo, useEffect, useRef, useState } from 'react';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';
import { FaLayerGroup } from 'react-icons/fa6';

import FlightCard from './FlightCard';
import MapLayersPanel from './MapLayersPanel';
import { useMapContext } from '../MapContext';
import MapToolbar from '../MapToolbar';
import { Project } from '../../pages/projects/ProjectList';

import { sortedFlightsByDateAndId } from './utils';

import uasIcon from '../../../assets/uas-icon.svg';

type ActiveProjectPaneProps = { project: Project };

export default function ActiveProjectPane({ project }: ActiveProjectPaneProps) {
  const { flights, activeDataProduct } = useMapContext();
  const scrollContainerRef = useRef<HTMLUListElement | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [shouldScrollOnMount, setShouldScrollOnMount] = useState(false);

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

  // Set flag when switching back to Flights tab with active data product
  useEffect(() => {
    if (selectedIndex === 0 && activeDataProduct) {
      setShouldScrollOnMount(true);
    }
  }, [selectedIndex, activeDataProduct]);

  // Scroll when the ref becomes available and flag is set
  useEffect(() => {
    if (shouldScrollOnMount && scrollContainerRef.current && activeDataProduct) {
      scrollToActiveDataProduct(100);
      setShouldScrollOnMount(false);
    }
  }, [shouldScrollOnMount, scrollContainerRef.current, activeDataProduct]);

  return (
    <article className="h-[calc(100%_-_44px)] p-4 flex flex-col">
      <header className="flex-none">
        <h1 className="truncate" title={project.title}>
          {project.title}
        </h1>
        <p className="text-slate-700 text-sm font-light line-clamp-2">
          {project.description}
        </p>
        <MapToolbar />
      </header>
      <TabGroup
        selectedIndex={selectedIndex}
        onChange={setSelectedIndex}
        className="flex-1 flex flex-col min-h-0"
      >
        <TabList className="flex gap-1 flex-none">
          <Tab className="data-[selected]:bg-slate-200 data-[hover]:bg-slate-100 focus:outline-none focus:ring-1 focus:ring-accent2 rounded px-3 py-1.5 text-sm font-medium whitespace-nowrap">
            <div className="flex items-center gap-1.5">
              <img
                src={uasIcon}
                alt=""
                className="h-3.5 w-3.5 data-[selected]:brightness-0"
              />
              <span>Flights</span>
            </div>
          </Tab>
          <Tab className="data-[selected]:bg-slate-200 data-[hover]:bg-slate-100 focus:outline-none focus:ring-1 focus:ring-accent2 rounded px-3 py-1.5 text-sm font-medium whitespace-nowrap">
            <div className="flex items-center gap-1.5">
              <FaLayerGroup className="h-3.5 w-3.5" />
              <span>Map Layers</span>
            </div>
          </Tab>
        </TabList>
        <hr className="my-2 border-slate-300 flex-none" />
        <TabPanels className="flex-1 min-h-0">
          <TabPanel className="h-full">
            <ul
              ref={scrollContainerRef}
              className="h-full space-y-2 overflow-y-auto pb-16"
            >
              {sortedFlights.length > 0 ? (
                sortedFlights.map((flight) => (
                  <li key={flight.id}>
                    <FlightCard flight={flight} />
                  </li>
                ))
              ) : (
                <div className="text-sm text-slate-500 italic p-2">
                  No flights found for this project. Add flights from the
                  project page.
                </div>
              )}
            </ul>
          </TabPanel>
          <TabPanel className="h-full overflow-y-auto pb-16">
            <MapLayersPanel />
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </article>
  );
}
