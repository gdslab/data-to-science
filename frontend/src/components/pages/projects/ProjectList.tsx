import axios from 'axios';
import { useEffect, useMemo, useState } from 'react';
import { useLoaderData, Link } from 'react-router-dom';

import { Button } from '../../Buttons';
import Modal from '../../Modal';
import Pagination, { getPaginationResults } from '../../Pagination';
import ProjectForm from './ProjectForm';
import { useProjectContext } from './ProjectContext';
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
  title: string;
  description: string;
  field: FieldGeoJSONFeature;
  flight_count: number;
  most_recent_flight: string;
  owner_id: string;
  is_owner: boolean;
  team_id: string;
  location_id: string;
}

export async function loader() {
  const response = await axios.get('/api/v1/projects');
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

function ProjectListHeader() {
  const [open, setOpen] = useState(false);

  const { locationDispatch } = useProjectContext();

  useEffect(() => {
    locationDispatch({ type: 'clear', payload: null });
  }, [open]);

  return (
    <div className="flex flex-col gap-4">
      <h1>Projects</h1>
      <div className="w-96">
        <Button icon="folderplus" onClick={() => setOpen(true)}>
          Create
        </Button>
        <Modal open={open} setOpen={setOpen}>
          <ProjectForm setModalOpen={setOpen} />
        </Modal>
      </div>
    </div>
  );
}

export default function ProjectList() {
  const [currentPage, setCurrentPage] = useState(0);
  const [sortSelection, setSortSelection] = useState<SortSelection>(
    getSortPreferenceFromLocalStorage('sortPreference')
  );

  const [searchText, setSearchText] = useState('');
  const projects = useLoaderData() as Project[];

  const { locationDispatch, project, projectDispatch } = useProjectContext();

  const MAX_ITEMS = 12;

  useEffect(() => {
    locationDispatch({ type: 'clear', payload: null });
    projectDispatch({ type: 'clear', payload: null });
  }, [project]);

  useEffect(() => {
    if (filterAndSlice(projects).length < MAX_ITEMS) {
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

  const TOTAL_PAGES = Math.ceil(filterSearch(projects).length / MAX_ITEMS);

  return (
    <div className="flex flex-col gap-4 p-4 h-full">
      {/* Project header and search */}
      <div className="flex flex-col gap-4">
        <ProjectListHeader />
        {!projects ||
          (projects.length === 0 && (
            <p>
              Use the above button to create your first project. Your projects will
              appear in the space below.
            </p>
          ))}
      </div>
      {projects && projects.length > 0 && (
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
              filterAndSlice(projects).length,
              filterSearch(projects).length
            )}
            <Sort sortSelection={sortSelection} setSortSelection={setSortSelection} />
          </div>
        </div>
      )}
      <div className="flex-1 flex flex-wrap gap-4 pb-24 overflow-y-auto">
        {useMemo(
          () => filterAndSlice(sortProjects(projects, sortSelection)),
          [currentPage, projects, searchText, sortSelection]
        ).map((project) => (
          <Link key={project.id} to={`/projects/${project.id}`} className="block h-36">
            <article className="flex items-center w-96 h-36 shadow bg-white transition hover:shadow-xl">
              <div className="w-32 h-full p-1.5 hidden sm:block">
                <img
                  className="h-full object-cover"
                  src={`/static/projects/${project.id}/preview_map.png`}
                />
              </div>

              <div className="w-full md:w-64 border-s border-gray-900/10 p-2 sm:border-l-transparent sm:p-4">
                <h3 className="font-bold uppercase text-gray-900 truncate">
                  {project.title}
                </h3>
                <p className="mt-2 line-clamp-3 text-sm/relaxed text-gray-700 text-wrap truncate">
                  {project.description}
                </p>
              </div>
            </article>
          </Link>
        ))}
      </div>
      {/* Pagination */}
      <div className="w-full bg-slate-200 fixed bottom-4 py-4 px-6">
        <div className="flex justify-center">
          <Pagination
            currentPage={currentPage}
            totalPages={TOTAL_PAGES}
            updateCurrentPage={updateCurrentPage}
          />
        </div>
      </div>
    </div>
  );
}
