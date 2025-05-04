import clsx from 'clsx';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PaperAirplaneIcon,
  StarIcon as StarIconOutline,
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

import { Button } from '../../Buttons';
import Filter from '../../Filter';
import LayerCard from './LayerCard';
import Pagination, { getPaginationResults } from '../../Pagination';
import { Project } from '../../pages/projects/ProjectList';
import ProjectSearch from '../../pages/projects/ProjectSearch';
import Sort, { sortProjects, SortSelection } from '../../Sort';
import { useMapContext } from '../MapContext';

import { getSortPreferenceFromLocalStorage } from '../../Sort';

const MAX_ITEMS = 10; // max number of projects per page in left-side pane

type ProjectsPaneProps = {
  projects: Project[] | null;
};

export default function ProjectsPane({ projects }: ProjectsPaneProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [openComponent, setOpenComponent] = useState<'filter' | 'sort' | null>(
    null
  );
  const [searchText, setSearchText] = useState('');
  const [sortSelection, setSortSelection] = useState<SortSelection>(
    getSortPreferenceFromLocalStorage('sortPreference')
  );

  const {
    activeDataProductDispatch,
    activeProjectDispatch,
    projectFilterSelection,
    projectFilterSelectionDispatch,
    projectsVisible,
  } = useMapContext();

  // Filter projects by filter selection
  const filteredProjects = useMemo(() => {
    if (!projects) return [];

    let filteredProjects = projects;

    if (projectFilterSelection.includes('myProjects')) {
      filteredProjects = filteredProjects.filter(
        (project) => project.role === 'owner'
      );
    }

    if (projectFilterSelection.includes('likedProjects')) {
      filteredProjects = filteredProjects.filter(
        (project) => project.liked || false
      );
    }

    return filteredProjects;
  }, [projects, projectFilterSelection]);

  // Filters projects by search text and visible projects in map extent
  const filteredVisibleProjects = useMemo(() => {
    if (!filteredProjects) return [];
    return filteredProjects
      .filter(({ id }) => projectsVisible.includes(id))
      .filter(
        (project) =>
          !project.title ||
          project.title.toLowerCase().includes(searchText.toLowerCase()) ||
          project.description.toLowerCase().includes(searchText.toLowerCase())
      );
  }, [filteredProjects, projectsVisible, searchText]);

  // Projects available on current page
  const currentPageProjects = useMemo(() => {
    return sortProjects(filteredVisibleProjects, sortSelection).slice(
      currentPage * MAX_ITEMS,
      MAX_ITEMS + currentPage * MAX_ITEMS
    );
  }, [currentPage, filteredVisibleProjects, sortSelection]);

  // Total number of pages
  const totalPages = useMemo(
    () => Math.ceil(filteredVisibleProjects.length / MAX_ITEMS),
    [filteredVisibleProjects]
  );

  // Activate clicked on project and clear any active data products
  const handleProjectClick = useCallback(
    (project: Project) => () => {
      activeDataProductDispatch({ type: 'clear', payload: null });
      activeProjectDispatch({ type: 'set', payload: project });
    },
    [activeDataProductDispatch, activeProjectDispatch]
  );

  // Update search text when user interacts with projects search bar
  const updateSearchText = useCallback((query: string) => {
    setSearchText(query);
  }, []);

  // Update current page when user interacts with pagination
  const updateCurrentPage = useCallback(
    (newPage: number): void => {
      if (newPage < 0) {
        setCurrentPage(0);
      } else if (newPage >= totalPages) {
        setCurrentPage(totalPages - 1);
      } else {
        setCurrentPage(newPage);
      }
    },
    [totalPages]
  );

  // Reset current page when there are fewer filtered visible projects than MAX_ITEMS
  useEffect(() => {
    if (filteredVisibleProjects.length <= MAX_ITEMS) {
      setCurrentPage(0);
    }
  }, [filteredVisibleProjects]);

  function updateProjectFilter(filterSelections: string[]) {
    projectFilterSelectionDispatch({ type: 'set', payload: filterSelections });
  }

  return (
    <div className="h-[calc(100%_-_44px)] p-4">
      <article className="h-full">
        <div className="h-36">
          <h1>Projects</h1>
          {filteredProjects && filteredProjects.length > 0 && (
            <div className="flex flex-col gap-2 my-2">
              <ProjectSearch
                searchText={searchText}
                updateSearchText={updateSearchText}
              />
              <div className="flex justify-between">
                {getPaginationResults(
                  currentPage,
                  MAX_ITEMS,
                  currentPageProjects.length,
                  filteredVisibleProjects.length
                )}
                <div className="flex flex-row gap-8">
                  <Filter
                    categories={[
                      { label: 'My projects', value: 'myProjects' },
                      { label: 'Favorite projects', value: 'likedProjects' },
                    ]}
                    selectedCategory={projectFilterSelection}
                    setSelectedCategory={updateProjectFilter}
                    isOpen={openComponent === 'filter'}
                    onOpen={() => setOpenComponent('filter')}
                    onClose={() => setOpenComponent(null)}
                  />
                  <Sort
                    sortSelection={sortSelection}
                    setSortSelection={setSortSelection}
                    isOpen={openComponent === 'sort'}
                    onOpen={() => setOpenComponent('sort')}
                    onClose={() => setOpenComponent(null)}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
        {filteredProjects && filteredProjects.length > 0 ? (
          <ul className="h-[calc(100%_-_144px)] space-y-2 overflow-y-auto pb-16">
            {currentPageProjects.map((project) => (
              <li key={project.id}>
                <LayerCard hover={true}>
                  <div
                    className="relative"
                    onClick={handleProjectClick(project)}
                    title={project.title}
                  >
                    <div className="absolute top-0 right-0">
                      {project.liked ? (
                        <StarIconSolid className="w-3 h-3 text-amber-500" />
                      ) : (
                        <StarIconOutline className="w-3 h-3 text-gray-400" />
                      )}
                    </div>
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
        ) : (
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
        )}
      </article>
      <div className="w-[450px] bg-slate-100 fixed bottom-0 p-2.5">
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          updateCurrentPage={updateCurrentPage}
        />
      </div>
    </div>
  );
}
