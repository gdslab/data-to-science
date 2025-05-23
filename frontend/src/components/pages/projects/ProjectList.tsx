import { useEffect, useMemo, useState } from 'react';

import LoadingBars from '../../LoadingBars';
import Filter from '../../Filter';
import Pagination, { getPaginationResults } from '../../Pagination';
import ProjectCard from './ProjectCard';
import { useProjectContext } from './ProjectContext';
import ProjectListHeader from './ProjectListHeader';
import ProjectSearch from './ProjectSearch';
import Sort, {
  SortSelection,
  getSortPreferenceFromLocalStorage,
  sortProjects,
} from '../../Sort';

interface FieldProperties {
  id: string;
  center_x: number;
  center_y: number;
}

type FieldGeoJSONFeature = Omit<GeoJSON.Feature, 'properties'> & {
  properties: FieldProperties;
};

export interface Project {
  id: string;
  centroid: {
    x: number;
    y: number;
  };
  data_product_count: number;
  description: string;
  field: FieldGeoJSONFeature;
  flight_count: number;
  liked: boolean;
  location_id: string;
  most_recent_flight: string;
  role: string;
  team_id: string;
  title: string;
}

export default function ProjectList({
  projects,
  revalidate,
}: {
  projects: Project[] | null;
  revalidate: () => void;
}) {
  const [currentPage, setCurrentPage] = useState(0);
  const [sortSelection, setSortSelection] = useState<SortSelection>(
    getSortPreferenceFromLocalStorage('sortPreference')
  );
  const [openComponent, setOpenComponent] = useState<'filter' | 'sort' | null>(
    null
  );

  const [searchText, setSearchText] = useState('');

  const {
    locationDispatch,
    project,
    projectDispatch,
    projectFilterSelection,
    projectFilterSelectionDispatch,
  } = useProjectContext();

  const MAX_ITEMS = 12;

  useEffect(() => {
    locationDispatch({ type: 'clear', payload: null });
    projectDispatch({ type: 'clear', payload: null });
  }, [project]);

  useEffect(() => {
    if (projects && filterAndSlice(projects).length < MAX_ITEMS) {
      setCurrentPage(0);
    }
  }, [searchText]);

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
    if (!projects) {
      setCurrentPage(0);
      return;
    }

    const total_pages = Math.ceil(projects.length / MAX_ITEMS);

    if (newPage + 1 > total_pages) {
      setCurrentPage(total_pages - 1);
    } else if (newPage < 0) {
      setCurrentPage(0);
    } else {
      setCurrentPage(newPage);
    }
  }

  /**
   * Filters projects by search text.
   * @param projs Projects to filter.
   * @returns
   */
  function filterSearch(projs: Project[]) {
    return projs.filter(
      (project) =>
        !project.title ||
        project.title.toLowerCase().includes(searchText.toLowerCase()) ||
        project.description.toLowerCase().includes(searchText.toLowerCase())
    );
  }

  /**
   * Filters projects by search text and limits to current page.
   * @param projs Projects to filter.
   * @returns Array of filtered and sliced projects.
   */
  function filterAndSlice(projs: Project[]): Project[] {
    return filterSearch(projs).slice(
      currentPage * MAX_ITEMS,
      MAX_ITEMS + currentPage * MAX_ITEMS
    );
  }

  const filteredProjects = useMemo(() => {
    if (!projects) {
      return [];
    }

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

  const filteredAndSortedProjects = useMemo(
    () =>
      filteredProjects
        ? filterAndSlice(sortProjects(filteredProjects, sortSelection))
        : [],
    [currentPage, filteredProjects, searchText, sortSelection]
  );

  const TOTAL_PAGES = Math.ceil(
    filteredProjects ? filterSearch(filteredProjects).length / MAX_ITEMS : 0
  );

  function updateProjectFilter(filterSelections: string[]) {
    projectFilterSelectionDispatch({ type: 'set', payload: filterSelections });
  }

  if (!filteredProjects) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center">
        <span className="text-lg italic text-gray-700 font-semibold">
          Checking for projects...
        </span>
        <LoadingBars />
      </div>
    );
  } else {
    return (
      <div className="flex flex-col gap-4 p-4 h-full">
        {/* Project header and search */}
        <div className="flex flex-col gap-4">
          <ProjectListHeader />
          {!filteredProjects ||
            (filteredProjects.length === 0 && (
              <p>
                Use the above button to create your first project. Your projects
                will appear in the space below.
              </p>
            ))}
        </div>
        {filteredProjects && filteredProjects.length > 0 && (
          <div>
            <div className="w-96 mb-4">
              <ProjectSearch
                searchText={searchText}
                updateSearchText={updateSearchText}
              />
            </div>
            <div className="flex justify-between">
              {/* Project cards */}
              {getPaginationResults(
                currentPage,
                MAX_ITEMS,
                filterAndSlice(filteredProjects).length,
                filterSearch(filteredProjects).length
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
        {filteredProjects && filteredProjects.length > 0 && (
          <div className="flex-1 flex flex-wrap gap-4 pb-24 overflow-y-auto">
            {filteredAndSortedProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                revalidate={revalidate}
              />
            ))}
          </div>
        )}
        {/* Pagination */}
        {filteredProjects && filteredProjects.length > 0 && (
          <div className="w-full bg-slate-200 fixed bottom-4 py-4 px-6">
            <div className="flex justify-center">
              <Pagination
                currentPage={currentPage}
                totalPages={TOTAL_PAGES}
                updateCurrentPage={updateCurrentPage}
              />
            </div>
          </div>
        )}
      </div>
    );
  }
}
