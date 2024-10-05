import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { PencilIcon } from '@heroicons/react/24/outline';

import { Button } from '../../../Buttons';
import Filter from '../../../Filter';
import FlightCarousel from './flights/FlightCarousel';
import FlightDeleteModal from './flights/FlightDeleteModal';
import FlightForm from './flights/FlightForm';
import Modal from '../../../Modal';
import TableCardRadioInput from '../../../TableCardRadioInput';
import { useProjectContext } from './ProjectContext';

import { getUnique, sorter } from '../../../utils';
import MoveFlightModal from './flights/MoveFlightModal';

function getFlightsDisplayModeFromLS(): 'table' | 'carousel' {
  const flightsDisplayMode = localStorage.getItem('flightsDisplayMode');
  if (flightsDisplayMode === 'table' || flightsDisplayMode === 'carousel') {
    return flightsDisplayMode;
  } else {
    localStorage.setItem('flightsDisplayMode', 'carousel');
    return 'carousel';
  }
}

export default function ProjectFlights() {
  const [flightSortOrder, setFlightSortOrder] = useState('asc');
  const [open, setOpen] = useState(false);
  const [tableView, toggleTableView] = useState<'table' | 'carousel'>(
    getFlightsDisplayModeFromLS()
  );

  const {
    flights,
    flightsFilterSelection,
    flightsFilterSelectionDispatch,
    project,
    projectRole,
  } = useProjectContext();

  function updateFlightsFilter(filterSelections: string[]) {
    flightsFilterSelectionDispatch({ type: 'set', payload: filterSelections });
  }

  function onTableViewChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === 'carousel' || e.target.value === 'table') {
      localStorage.setItem('flightsDisplayMode', e.target.value);
      toggleTableView(e.target.value);
    }
  }

  const sortedFlights = useMemo(
    () =>
      flights &&
      flights
        .filter(({ sensor }) => flightsFilterSelection.indexOf(sensor) > -1)
        .sort((a, b) =>
          sorter(
            new Date(a.acquisition_date),
            new Date(b.acquisition_date),
            flightSortOrder
          )
        ),
    [flights, flightsFilterSelection, flightSortOrder]
  );

  return (
    <div className="grow min-h-0">
      <div className="h-full flex flex-col gap-4">
        <div className="h-24">
          <h2>Flights</h2>
          <div className="flex justify-between">
            <div className="flex flex-row gap-8">
              <div className="flex flex-row items-center gap-2">
                <label
                  htmlFor="flightSortOrder"
                  className="text-sm font-medium text-gray-900 w-20"
                >
                  Sort by
                </label>
                <select
                  name="flightSortOrder"
                  id="flightSortOrder"
                  className="w-full px-1.5 font-semibold rounded-md border-2 border-zinc-300 text-gray-700 sm:text-sm"
                  onChange={(e) => setFlightSortOrder(e.target.value)}
                >
                  <option value="asc">Date (ascending)</option>
                  <option value="desc">Date (descending)</option>
                </select>
              </div>
              {flights && flights.length > 0 && (
                <div className="flex flex-row items-center gap-2">
                  <Filter
                    categories={getUnique(flights, 'sensor')}
                    selectedCategory={flightsFilterSelection}
                    setSelectedCategory={updateFlightsFilter}
                  />
                </div>
              )}
            </div>
            <TableCardRadioInput
              tableView={tableView}
              toggleTableView={onTableViewChange}
            />
          </div>
        </div>

        {project && flights && flights.length > 0 && tableView === 'table' && (
          <div className="min-w-[1000px] overflow-x-auto">
            <div className="overflow-y-auto min-h-96 max-h-96 xl:max-h-[420px] 2xl:max-h-[512px]">
              <table className="w-full table-auto border-collapse">
                <thead className="h-full sticky top-0 bg-[#e2e8f0]">
                  <tr className="whitespace-nowrap font-semibold text-slate-600">
                    <th scope="col" className="px-4 py-2">
                      Name
                    </th>
                    <th scope="col" className="px-4 py-2">
                      Platform
                    </th>
                    <th scope="col" className="px-4 py-2 w-40">
                      Sensor
                    </th>
                    <th scope="col" className="px-4 py-2 w-48">
                      Acquisition Date
                    </th>
                    <th scope="col" className="px-4 py-2 w-24">
                      Data
                    </th>
                    {projectRole !== 'viewer' && (
                      <th scope="col" className="px-4 py-2 w-64">
                        Actions
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {(sortedFlights || []).map((flight, index) => (
                    <tr
                      key={`tablerow::${index}`}
                      className="text-center whitespace-nowrap"
                    >
                      <td className="p-1 max-w-96">
                        <div className="bg-white p-4 text-ellipsis overflow-hidden ...">
                          {flight.name || 'No name'}
                        </div>
                      </td>
                      <td className="p-1 max-w-80">
                        <div className="bg-white p-4 text-ellipsis overflow-hidden ...">
                          {flight.platform.replace(/_/g, ' ')}
                        </div>
                      </td>
                      <td className="p-1">
                        <div className="bg-white p-4">{flight.sensor}</div>
                      </td>
                      <td className="p-1">
                        <div className="bg-white p-4">{flight.acquisition_date}</div>
                      </td>
                      <td className="p-1">
                        <div className="bg-white p-4">
                          <Link
                            className="!text-sky-600 visited:text-sky-600"
                            to={`/projects/${project.id}/flights/${flight.id}/data`}
                          >
                            Manage
                          </Link>
                        </div>
                      </td>
                      {projectRole !== 'viewer' && (
                        <td className="p-1">
                          <div className="flex items-center justify-between gap-4 p-4 bg-white">
                            <Link
                              className="!text-sky-600 visited:text-sky-600"
                              to={`/projects/${project.id}/flights/${flight.id}/edit`}
                            >
                              <div className="flex items-center gap-2">
                                <PencilIcon className="h-4 w-4" />
                                <span>Edit</span>
                              </div>
                            </Link>
                            {projectRole === 'owner' && (
                              <MoveFlightModal
                                flightId={flight.id}
                                srcProjectId={flight.project_id}
                                tableView={true}
                              />
                            )}
                            {projectRole === 'owner' && (
                              <FlightDeleteModal flight={flight} tableView={true} />
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {project && flights && flights.length > 0 && tableView === 'carousel' && (
          <div className="h-full min-h-96 mx-4">
            <FlightCarousel flights={sortedFlights || []} />
          </div>
        )}

        {projectRole !== 'viewer' ? (
          <div className="my-4 flex justify-center">
            <Modal open={open} setOpen={setOpen}>
              <FlightForm setOpen={setOpen} />
            </Modal>
            <Button size="sm" onClick={() => setOpen(true)}>
              Add New Flight
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
