import clsx from 'clsx';
import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  ArrowUturnLeftIcon,
  Bars3Icon,
  MapIcon,
  PaperAirplaneIcon,
  ScaleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import { Button } from '../Buttons';
import { getDataProductName } from '../pages/projects/flights/dataProducts/DataProductsTable';
import HintText from '../HintText';
import { useMapContext } from './MapContext';
import Pagination, { getPaginationResults } from '../Pagination';
import { Band } from '../pages/projects/Project';
import { Project } from '../pages/projects/ProjectList';
import ProjectSearch from '../pages/projects/ProjectSearch';
import Sort, { SortSelection, sortProjects } from '../Sort';
import SymbologyControls from './SymbologyControls';

import { getDefaultStyle } from './utils';

import UASIcon from '../../assets/uas-icon.svg';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

function MapToolbar() {
  const {
    activeMapTool,
    activeDataProductDispatch,
    activeMapToolDispatch,
    tileScaleDispatch,
  } = useMapContext();
  return (
    <fieldset className="border border-solid border-slate-300 p-1.5">
      <legend>Map Tools</legend>
      <div className="flex items-end justify-start gap-1.5">
        <div
          className={classNames(
            activeMapTool === 'map' ? 'bg-accent2' : '',
            'h-8 w-8 cursor-pointer shadow-sm hover:shadow-xl rounded border-2 border-solid border-slate-500 p-1.5'
          )}
          onClick={() => {
            activeDataProductDispatch({ type: 'clear', payload: null });
            activeMapToolDispatch({ type: 'set', payload: 'map' });
          }}
        >
          <MapIcon className="h-4 w-4" />
          <span className="sr-only">Map Tool</span>
        </div>
        <div
          className={classNames(
            activeMapTool === 'compare' ? 'bg-accent2' : '',
            'h-8 w-8 cursor-pointer shadow-sm hover:shadow-xl rounded border-2 border-solid border-slate-500 p-1.5'
          )}
          onClick={() => {
            activeDataProductDispatch({ type: 'clear', payload: null });
            activeMapToolDispatch({ type: 'set', payload: 'compare' });
          }}
        >
          <ScaleIcon className="h-4 w-4" />
          <span className="sr-only">Compare Tool</span>
        </div>
        <div className="mt-4">
          <input
            id="scale-checkbox"
            type="checkbox"
            name="scale"
            className="size-4 rounded text-accent2 border-gray-300"
            onChange={(e) => {
              tileScaleDispatch({
                type: 'set',
                payload: e.currentTarget.checked ? 4 : 2,
              });
            }}
          />
          <label
            htmlFor="scale-checkbox"
            className="ms-2 text-sm font-medium text-gray-900 dark:text-gray-300"
            title="Increases tile resolution from 512x512 to 1024x1024"
          >
            Increase tile resolution
          </label>
        </div>
      </div>
    </fieldset>
  );
}

function LayerCard({
  active = false,
  children,
  hover = false,
}: {
  active?: boolean;
  children: React.ReactNode;
  hover?: boolean;
}) {
  return (
    <div
      className={classNames(
        active ? 'border-slate-400' : 'border-slate-200',
        hover && !active ? 'cursor-pointer hover:border-2 hover:shadow-md' : '',
        'p-2 rounded-sm shadow-sm bg-white border-solid border-2'
      )}
    >
      {children}
    </div>
  );
}

export function formatDate(datestring) {
  return new Date(datestring).toLocaleDateString('en-us', {
    timeZone: 'UTC',
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function RasterStats({ stats }: { stats: Band['stats'] }) {
  return (
    <div className="grid grid-cols-4 gap-1.5">
      <span>Mean: {stats.mean.toFixed(2)}</span>
      <span>Min: {stats.minimum.toFixed(2)}</span>
      <span>Max: {stats.maximum.toFixed(2)}</span>
      <span>Std. Dev: {stats.stddev.toFixed(2)}</span>
    </div>
  );
}

/**
 * Checks local storage for previously stored projects.
 * @returns Array of projects retrieved from local storage.
 */
function getLocalStorageProjects(): Project[] | null {
  if ('projects' in localStorage) {
    const lsProjectsString = localStorage.getItem('projects');
    if (lsProjectsString) {
      const lsProjects: Project[] = JSON.parse(lsProjectsString);
      if (lsProjects && lsProjects.length > 0) {
        return lsProjects;
      }
    }
  }

  return null;
}

export default function LayerPane({
  hidePane,
  toggleHidePane,
}: {
  hidePane: boolean;
  toggleHidePane: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const [currentPage, setCurrentPage] = useState(0);
  const [mapProjects, setMapProjects] = useState<Project[] | null>(
    getLocalStorageProjects()
  );
  const [searchText, setSearchText] = useState('');
  const [sortSelection, setSortSelection] = useState<SortSelection>('atoz');

  const {
    activeDataProduct,
    activeDataProductDispatch,
    activeMapToolDispatch,
    activeProject,
    activeProjectDispatch,
    flights,
    projects,
    projectsVisible,
    symbologySettingsDispatch,
  } = useMapContext();

  const { state } = useLocation();

  const MAX_ITEMS = 10; // max number of projects per page in left-side pane

  useEffect(() => {
    if (projects) {
      setMapProjects(projects);
    }
  }, [projects]);

  useEffect(() => {
    // hide left-side pane when point cloud dataset is activated
    if (activeDataProduct && activeDataProduct.data_type === 'point_cloud') {
      toggleHidePane(true);
    }
  }, [activeDataProduct]);

  useEffect(() => {
    // reset to page one if the number of visible project markers
    // on the map is less than or equal to the max items allowed on a page
    if (projectsVisible.length <= MAX_ITEMS) {
      setCurrentPage(0);
    }
  }, [projectsVisible]);

  useEffect(() => {
    // reset to page one if the filtered number of projects
    // is less than or equal to the max items allowed on a page
    if (filterByVisibilityAndSearch(mapProjects).length <= MAX_ITEMS) {
      setCurrentPage(0);
    }
  }, [searchText]);

  useEffect(() => {
    if (state && state.project && state.dataProduct) {
      activeProjectDispatch({ type: 'set', payload: state.project });
      activeDataProductDispatch({ type: 'set', payload: state.dataProduct });
      if (state.dataProduct.user_style) {
        symbologySettingsDispatch({
          type: 'update',
          payload: state.dataProduct.user_style,
        });
      } else if (state.dataProduct.data_type !== 'point_cloud') {
        symbologySettingsDispatch({
          type: 'update',
          payload: getDefaultStyle(state.dataProduct),
        });
      }
    }
  }, [state]);

  /**
   * Updates the current search text.
   */
  function updateSearchText(query: string) {
    setSearchText(query);
  }

  /**
   * Updates the current selected pagination page.
   * @param newPage Index of new page.
   */
  function updateCurrentPage(newPage: number): void {
    const total_pages = Math.ceil(mapProjects ? mapProjects.length : 0 / MAX_ITEMS);

    if (newPage + 1 > total_pages) {
      setCurrentPage(total_pages - 1);
    } else if (newPage < 0) {
      setCurrentPage(0);
    } else {
      setCurrentPage(newPage);
    }
  }

  /**
   * Filters projects by visible markers on map and search text.
   * @param projs Projects to filter.
   * @returns
   */
  function filterByVisibilityAndSearch(projs): Project[] {
    if (!projs) {
      return [];
    } else {
      return projs
        .filter(({ id }) =>
          projects
            ? projectsVisible.includes(id)
            : mapProjects
            ? mapProjects.map(({ id }) => id).includes(id)
            : []
        )
        .filter(
          (project) =>
            !project.title ||
            project.title.toLowerCase().includes(searchText.toLowerCase()) ||
            project.description.toLowerCase().includes(searchText.toLowerCase())
        );
    }
  }

  const TOTAL_PAGES = Math.ceil(
    filterByVisibilityAndSearch(mapProjects).length / MAX_ITEMS
  );

  /**
   * Filters projects by search text and limits to current page.
   * @param projs Projects to filter.
   * @returns
   */
  function filterAndSlice(projs: Project[]) {
    return filterByVisibilityAndSearch(projs).slice(
      currentPage * MAX_ITEMS,
      MAX_ITEMS + currentPage * MAX_ITEMS
    );
  }

  /**
   * Returns available projects based on visibility, search text,
   * page limitations. Returned projects are sorted in alphabetical order.
   * @param projs Projects to filter, limit, and sort.
   * @returns Array of filtered projects.
   */
  function getAvailableProjects(projs): Project[] {
    return filterAndSlice(sortProjects(projs, sortSelection));
  }

  if (hidePane) {
    return (
      <div className="flex items-center justify-between p-2.5 text-slate-700">
        <button type="button">
          <Bars3Icon
            className="h-6 w-6 cursor-pointers"
            onClick={() => toggleHidePane(!hidePane)}
          />
        </button>
      </div>
    );
  } else {
    return (
      <div className="flex flex-col h-full">
        <div className="flex-1 flex flex-col pb-12 text-slate-700 overflow-y-auto">
          <div className="flex items-center justify-between p-2.5">
            {activeProject ? (
              <button
                type="button"
                onClick={() => {
                  activeMapToolDispatch({ type: 'set', payload: 'map' });
                  activeProjectDispatch({ type: 'clear', payload: null });
                }}
              >
                <ArrowUturnLeftIcon className="h-6 w-6 cursor-pointer" />
              </button>
            ) : (
              <span></span>
            )}
            <XMarkIcon
              className="h-6 w-6 cursor-pointer float-right"
              onClick={() => toggleHidePane(!hidePane)}
            />
          </div>
          {activeProject ? (
            <article className="p-4 overflow-y-auto">
              <h1>{activeProject.title}</h1>
              <HintText>{activeProject.description}</HintText>
              <MapToolbar />
              <ul className="mt-4 space-y-2">
                {flights
                  .sort((a, b) =>
                    new Date(a.acquisition_date) < new Date(b.acquisition_date) ? 1 : -1
                  )
                  .map((flight) => (
                    <li key={flight.id}>
                      <LayerCard>
                        <div className="grid grid-cols-6">
                          <div className="col-span-1 flex items-center justify-center">
                            <img src={UASIcon} width={'50%'} />
                          </div>
                          <div className="col-span-5 flex flex-col items-start gap-2">
                            <strong className="font-bold text-slate-700">
                              {formatDate(flight.acquisition_date)}
                            </strong>
                            <div className="grid grid-rows-2 text-slate-700 text-sm gap-1.5">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <span className="text-sm text-slate-400 font-semibold">
                                    Platform:{' '}
                                  </span>
                                  {flight.platform.replace('_', ' ')}
                                </div>
                                <div>
                                  <span className="text-sm text-slate-400 font-semibold">
                                    Sensor:
                                  </span>{' '}
                                  {flight.sensor}
                                </div>
                              </div>
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <span className="text-sm text-slate-400 font-semibold">
                                    Altitude (m):
                                  </span>{' '}
                                  {flight.altitude}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                        {flight.data_products.length > 0 ? (
                          <details
                            className="group space-y-2 [&_summary::-webkit-details-marker]:hidden text-slate-600 overflow-visible"
                            open={
                              activeDataProduct &&
                              activeDataProduct.flight_id === flight.id
                                ? true
                                : false
                            }
                          >
                            <summary className="text-sm cursor-pointer">{`${flight.data_products.length} Data Products`}</summary>
                            {flight.data_products.map((dataProduct) => (
                              <LayerCard
                                key={dataProduct.id}
                                hover={true}
                                active={
                                  activeDataProduct &&
                                  dataProduct.id === activeDataProduct.id
                                    ? true
                                    : false
                                }
                              >
                                <div className="text-slate-600 text-sm">
                                  <div
                                    className="grid grid-flow-row auto-rows-max"
                                    onClick={() => {
                                      if (
                                        (dataProduct && !activeDataProduct) ||
                                        (dataProduct &&
                                          activeDataProduct &&
                                          dataProduct.id !== activeDataProduct.id)
                                      ) {
                                        activeDataProductDispatch({
                                          type: 'set',
                                          payload: dataProduct,
                                        });
                                        if (dataProduct.user_style) {
                                          symbologySettingsDispatch({
                                            type: 'update',
                                            payload: dataProduct.user_style,
                                          });
                                        } else if (
                                          dataProduct.data_type !== 'point_cloud'
                                        ) {
                                          symbologySettingsDispatch({
                                            type: 'update',
                                            payload: getDefaultStyle(dataProduct),
                                          });
                                        }
                                      }
                                    }}
                                  >
                                    <strong>
                                      {getDataProductName(dataProduct.data_type)}
                                    </strong>
                                    {dataProduct.data_type !== 'point_cloud' ? (
                                      <fieldset className="border border-solid border-slate-300 p-3">
                                        <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                                          Band Info
                                        </legend>
                                        <div className="flex flex-row flex-wrap justify-start gap-1.5">
                                          {dataProduct.stac_properties.eo.map((b) => {
                                            return (
                                              <span key={b.name} className="mr-2">
                                                {b.name} ({b.description})
                                              </span>
                                            );
                                          })}
                                        </div>
                                      </fieldset>
                                    ) : null}
                                    {dataProduct.data_type !== 'point_cloud' ? (
                                      <div className="grid grid-flow-col auto-cols-max gap-1.5">
                                        {dataProduct.stac_properties.raster.length ===
                                        1 ? (
                                          <RasterStats
                                            stats={
                                              dataProduct.stac_properties.raster[0]
                                                .stats
                                            }
                                          />
                                        ) : null}
                                      </div>
                                    ) : null}
                                  </div>
                                  {activeDataProduct &&
                                  activeDataProduct.id === dataProduct.id &&
                                  dataProduct.data_type !== 'point_cloud' ? (
                                    <div className="mt-2">
                                      <SymbologyControls
                                        numOfBands={
                                          dataProduct.stac_properties
                                            ? dataProduct.stac_properties.raster.length
                                            : 1 // default to single band
                                        }
                                      />{' '}
                                    </div>
                                  ) : null}
                                </div>
                              </LayerCard>
                            ))}
                          </details>
                        ) : null}
                      </LayerCard>
                    </li>
                  ))}
              </ul>
            </article>
          ) : (
            <article className="flex flex-col p-4 overflow-y-auto overflow-x-hidden">
              <h1>Projects</h1>
              {mapProjects && mapProjects.length > 0 ? (
                <div className="flex flex-col gap-2 my-2">
                  <ProjectSearch
                    searchText={searchText}
                    updateSearchText={updateSearchText}
                  />
                  <div className="flex justify-between">
                    {getPaginationResults(
                      currentPage,
                      MAX_ITEMS,
                      filterAndSlice(mapProjects).length,
                      filterByVisibilityAndSearch(mapProjects).length
                    )}
                    <Sort
                      sortSelection={sortSelection}
                      setSortSelection={setSortSelection}
                    />
                  </div>
                </div>
              ) : null}
              {mapProjects && mapProjects.length > 0 ? (
                <ul className="space-y-2 overflow-y-auto">
                  {getAvailableProjects(mapProjects).map((project) => (
                    <li key={project.id}>
                      <LayerCard hover={true}>
                        <div
                          onClick={() => {
                            activeDataProductDispatch({ type: 'clear', payload: null });
                            activeProjectDispatch({ type: 'set', payload: project });
                          }}
                        >
                          <div className="grid grid-cols-4 gap-4">
                            <div className="flex items-center justify-between">
                              <img
                                className="object-cover w-16"
                                src={`/static/projects/${project.id}/preview_map.png`}
                                alt="Image of project boundary"
                              />
                            </div>
                            <div className="col-span-2 flex flex-col items-start gap-2">
                              <strong className="font-bold text-slate-700 line-clamp-1">
                                {project.title}
                              </strong>
                              <div className="text-slate-700 text-sm line-clamp-1">
                                {project.description}
                              </div>
                            </div>
                            <div className="flex items-center justify-center">
                              <span
                                className={clsx(
                                  'inline-flex items-center justify-center rounded-full text-sky-700 px-2.5 py-0.5',
                                  {
                                    'bg-sky-50': project.flight_count === 0,
                                    'bg-sky-100':
                                      project.flight_count > 0 &&
                                      project.flight_count < 5,
                                    'bg-sky-200': project.flight_count > 4,
                                  }
                                )}
                              >
                                <PaperAirplaneIcon className="h-4 w-4 -ms-1 me-1.5" />
                                <p className="whitespace-nowrap text-sm">
                                  {project.flight_count} Flights
                                </p>
                              </span>
                            </div>
                          </div>
                        </div>
                      </LayerCard>
                    </li>
                  ))}
                </ul>
              ) : mapProjects && mapProjects.length === 0 ? (
                <div>
                  <p className="mb-4">
                    You do not have any projects to display on the map. Use the below
                    button to navigate to the Projects page and create your first
                    project.
                  </p>
                  <Link to="/projects">
                    <Button>My Projects</Button>
                  </Link>
                </div>
              ) : (
                <div className="w-full">
                  <div className="h-1.5 w-full bg-blue-100 rounded-lg overflow-hidden">
                    <div className="animate-progress w-full h-full bg-blue-500 origin-left-right"></div>
                  </div>
                </div>
              )}
            </article>
          )}
        </div>

        <div className="w-[450px] bg-slate-100 fixed bottom-0 p-2.5">
          <Pagination
            currentPage={currentPage}
            totalPages={TOTAL_PAGES}
            updateCurrentPage={updateCurrentPage}
          />
        </div>
      </div>
    );
  }
}
