import clsx from 'clsx';
import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  ArrowUturnLeftIcon,
  Bars3Icon,
  PaperAirplaneIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import { useMapContext } from '../MapContext';

import { Button } from '../../Buttons';
import FlightCard from './FlightCard';
import LayerCard from './LayerCard';
import MapToolbar from '../MapToolbar';
import Pagination, { getPaginationResults } from '../../Pagination';
import { Project } from '../../pages/projects/ProjectList';
import ProjectSearch from '../../pages/projects/ProjectSearch';
import Sort, {
  getSortPreferenceFromLocalStorage,
  SortSelection,
  sortProjects,
} from '../../Sort';

import { getLocalStorageProjects } from './utils';
import { getDefaultStyle } from '../utils';

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
  const [sortSelection, setSortSelection] = useState<SortSelection>(
    getSortPreferenceFromLocalStorage('sortPreference')
  );

  const {
    activeDataProduct,
    activeDataProductDispatch,
    activeMapTool,
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
    // hide left-side pane when compare mode turned on
    if (activeMapTool === 'compare') {
      toggleHidePane(true);
    }
  }, [activeMapTool]);

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

  // sort flights by date, followed by id if the dates are a match
  const sortedFlights = useMemo(() => {
    const sorted = [...flights];
    sorted.sort((a, b) => {
      const dateA = new Date(a.acquisition_date);
      const dateB = new Date(b.acquisition_date);
      if (dateA < dateB) return -1;
      if (dateA > dateB) return 1;
      if (a.id < b.id) return -1;
      if (a.id > b.id) return 1;
      return 0;
    });
    return sorted;
  }, [flights]);

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
      <div className="h-full flex flex-col">
        <div className="h-full text-slate-700">
          <div className="h-11 flex items-center justify-between p-2.5">
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
            <article className="h-[calc(100%_-_44px)] p-4">
              <div className="h-44">
                <h1 className="truncate">{activeProject.title}</h1>
                <p className="text-slate-700 text-sm font-light line-clamp-2">
                  {activeProject.description}
                </p>
                <MapToolbar />
              </div>
              <ul className="h-[calc(100%_-_160px)] space-y-2 overflow-y-auto pb-16">
                {sortedFlights.map((flight) => (
                  <li key={flight.id}>
                    <FlightCard flight={flight} />
                  </li>
                ))}
              </ul>
            </article>
          ) : (
            <article className="h-[calc(100%_-_44px)] p-4">
              <div className="h-36">
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
              </div>
              {mapProjects && mapProjects.length > 0 ? (
                <ul className="h-[calc(100%_-_144px)] space-y-2 overflow-y-auto pb-16">
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

        {!activeProject && (
          <div className="w-[450px] bg-slate-100 fixed bottom-0 p-2.5">
            <Pagination
              currentPage={currentPage}
              totalPages={TOTAL_PAGES}
              updateCurrentPage={updateCurrentPage}
            />
          </div>
        )}
      </div>
    );
  }
}
