import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PencilIcon } from '@heroicons/react/24/outline';

import { Button } from '../../Buttons';
import Filter from '../../Filter';
import FlightCarousel from './flights/FlightCarousel';
import FlightDeleteModal from './flights/FlightDeleteModal';
import FlightForm from './flights/FlightForm';
import Modal from '../../Modal';
import Table, { TableBody, TableHead } from '../../Table';
import TableCardRadioInput from '../../TableCardRadioInput';
import { useProjectContext } from './ProjectContext';

import { getUnique, sorter } from '../../utils';

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

  const flightColumns = [
    'Name',
    'Platform',
    'Sensor',
    'Acquisition Date',
    'Data',
    'Actions',
  ];

  function updateFlightsFilter(filterSelections: string[]) {
    flightsFilterSelectionDispatch({ type: 'set', payload: filterSelections });
  }

  function onTableViewChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === 'carousel' || e.target.value === 'table') {
      localStorage.setItem('flightsDisplayMode', e.target.value);
      toggleTableView(e.target.value);
    }
  }

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
              {flights && flights.length > 0 ? (
                <div className="flex flex-row items-center gap-2">
                  <Filter
                    categories={getUnique(flights, 'sensor')}
                    selectedCategory={flightsFilterSelection}
                    setSelectedCategory={updateFlightsFilter}
                  />
                </div>
              ) : null}
            </div>
            <TableCardRadioInput
              tableView={tableView}
              toggleTableView={onTableViewChange}
            />
          </div>
        </div>
        {project && flights && flights.length > 0 ? (
          tableView === 'table' ? (
            <Table>
              <TableHead
                columns={
                  projectRole === 'viewer'
                    ? flightColumns.slice(0, flightColumns.length - 1)
                    : flightColumns
                }
              />
              <TableBody
                rows={flights
                  .filter(({ sensor }) => flightsFilterSelection.indexOf(sensor) > -1)
                  .sort((a, b) =>
                    sorter(
                      new Date(a.acquisition_date),
                      new Date(b.acquisition_date),
                      flightSortOrder
                    )
                  )
                  .map((flight) => ({
                    key: flight.id,
                    values: [
                      flight.name ? flight.name : '',
                      flight.platform.replace(/_/g, ' '),
                      flight.sensor,
                      flight.acquisition_date,
                      <Link
                        className="!text-sky-600 visited:text-sky-600"
                        to={`/projects/${project.id}/flights/${flight.id}/data`}
                      >
                        Manage
                      </Link>,
                    ],
                  }))}
                actions={
                  projectRole === 'viewer'
                    ? undefined
                    : flights
                        .filter(
                          ({ sensor }) => flightsFilterSelection.indexOf(sensor) > -1
                        )
                        .sort((a, b) =>
                          sorter(
                            new Date(a.acquisition_date),
                            new Date(b.acquisition_date),
                            flightSortOrder
                          )
                        )
                        .map((flight) => {
                          const editAction = {
                            key: `action-edit-${flight.id}`,
                            icon: <PencilIcon className="h-4 w-4" />,
                            label: 'Edit',
                            url: `/projects/${project.id}/flights/${flight.id}/edit`,
                          };
                          const deleteAction = {
                            key: `action-delete-${flight.id}`,
                            type: 'component',
                            component: (
                              <FlightDeleteModal flight={flight} tableView={true} />
                            ),
                            label: 'Delete',
                          };
                          if (projectRole === 'owner')
                            return [editAction, deleteAction];
                          return [editAction];
                        })
                }
              />
            </Table>
          ) : (
            <div className="h-full min-h-96 mx-4">
              <FlightCarousel
                flights={flights.filter(
                  ({ sensor }) => flightsFilterSelection.indexOf(sensor) > -1
                )}
                sortOrder={flightSortOrder}
              />
            </div>
          )
        ) : null}
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
