import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router';
import {
  PaperAirplaneIcon,
  StarIcon as StarIconOutline,
  UserGroupIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

import { Button } from '../../Buttons';
import CountBadge from '../../CountBadge';
import Filter from '../../Filter';
import LayerCard from './LayerCard';
import Pagination, { getPaginationResults } from '../../Pagination';
import { ProjectItem } from '../../pages/projects/Project';
import ProjectSearch from '../../pages/projects/ProjectSearch';
import Sort, { sortProjects, SortSelection } from '../../Sort';
import { useMapContext } from '../MapContext';

import { getSortPreferenceFromLocalStorage } from '../../Sort';
import { getCategory } from '../utils';
const MAX_ITEMS = 10; // max number of projects per page in left-side pane

type ProjectsPaneProps = {
  projects: ProjectItem[] | null;
};

export default function ProjectsPane({ projects }: ProjectsPaneProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [openComponent, setOpenComponent] = useState<
    'filter' | 'sort' | 'teamFilter' | null
  >(null);
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
    selectedTeamIds,
    selectedTeamIdsDispatch,
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

    if (
      projectFilterSelection.includes('myTeams') &&
      selectedTeamIds.length > 0
    ) {
      filteredProjects = filteredProjects.filter(
        (project) => project.team && selectedTeamIds.includes(project.team.id)
      );
    }

    return filteredProjects;
  }, [projects, projectFilterSelection, selectedTeamIds]);

  const teamCategories = useMemo(() => {
    if (!projects) return [] as { label: string; value: string }[];
    const unique = new Map<string, string>();
    projects.forEach((p) => {
      if (p.team) {
        unique.set(p.team.id, p.team.title);
      }
    });
    return Array.from(unique.entries())
      .map(([id, title]) => ({ label: title, value: id }))
      .sort((a, b) =>
        a.label.localeCompare(b.label, undefined, { sensitivity: 'base' })
      );
  }, [projects]);

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
    (project: ProjectItem) => () => {
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
    <div className="h-[calc(100%-44px)] p-4 flex flex-col">
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
                    { label: 'My teams', value: 'myTeams' },
                  ]}
                  selectedCategory={projectFilterSelection}
                  setSelectedCategory={updateProjectFilter}
                  isOpen={openComponent === 'filter'}
                  onOpen={() => setOpenComponent('filter')}
                  onClose={() => setOpenComponent(null)}
                  sublistParentValue="myTeams"
                  sublistCategories={teamCategories}
                  sublistSelected={selectedTeamIds}
                  setSublistSelected={(teamIds) =>
                    selectedTeamIdsDispatch({ type: 'set', payload: teamIds })
                  }
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
      <div className="flex-1 min-h-0">
        {filteredProjects && filteredProjects.length > 0 ? (
          <ul className="h-full space-y-2 overflow-y-auto">
            {currentPageProjects.map((project) => (
              <li key={project.id}>
                <LayerCard hover={true}>
                  <div
                    className="relative pr-4 pt-1"
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
                        <div className="flex flex-col items-start gap-1">
                          <CountBadge
                            count={project.flight_count}
                            color="sky"
                            label="Flights"
                            icon={
                              <PaperAirplaneIcon className="h-4 w-4 -ms-1 me-1.5" />
                            }
                            rank={getCategory(
                              project.data_product_count,
                              'flight'
                            )}
                          />
                          {project.team ? (
                            <span
                              className="inline-flex items-center justify-center rounded-full px-2.5 py-0.5 bg-indigo-50 text-indigo-700"
                              title={project.team.title}
                            >
                              <UserGroupIcon className="h-4 w-4 -ms-1 me-1.5" />
                              <p className="whitespace-nowrap text-xs">Team</p>
                            </span>
                          ) : null}
                        </div>
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
      </div>
      <div className="bg-slate-100 p-2.5">
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          updateCurrentPage={updateCurrentPage}
        />
      </div>
    </div>
  );
}
