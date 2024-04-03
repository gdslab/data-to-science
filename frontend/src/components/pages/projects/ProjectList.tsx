import axios from 'axios';
import { useEffect, useState } from 'react';
import { useLoaderData, Link } from 'react-router-dom';

import { Button } from '../../Buttons';
import Modal from '../../Modal';
import Pagination from '../../Pagination';
import ProjectForm from './ProjectForm';
import { useProjectContext } from './ProjectContext';
import ProjectSearch from './ProjectSearch';

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

export default function ProjectList() {
  const [currentPage, setCurrentPage] = useState(0);
  const [open, setOpen] = useState(false);
  const [searchText, setSearchText] = useState('');
  const projects = useLoaderData() as Project[];

  const { locationDispatch, project, projectDispatch } = useProjectContext();

  const MAX_ITEMS = 10;

  useEffect(() => {
    locationDispatch({ type: 'clear', payload: null });
  }, [open]);

  useEffect(() => {
    locationDispatch({ type: 'clear', payload: null });
    projectDispatch({ type: 'clear', payload: null });
  }, [project]);

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
   * @returns
   */
  function filterAndSlice(projs: Project[]) {
    return filterSearch(projs).slice(
      currentPage * MAX_ITEMS,
      MAX_ITEMS + currentPage * MAX_ITEMS
    );
  }

  const TOTAL_PAGES = Math.ceil(
    projects.filter(
      (project) =>
        !project.title ||
        project.title.toLowerCase().includes(searchText.toLowerCase()) ||
        project.description.toLowerCase().includes(searchText.toLowerCase())
    ).length / MAX_ITEMS
  );

  function getPaginationResults() {
    if (filterAndSlice(projects).length === 1 && currentPage === 0) {
      return <span className="text-sm text-gray-600">Viewing 1 of 1</span>;
    } else {
      return (
        <span className="text-sm text-gray-600">
          Viewing {currentPage * MAX_ITEMS + 1} -{' '}
          {currentPage * MAX_ITEMS + filterAndSlice(projects).length} of{' '}
          {filterSearch(projects).length < MAX_ITEMS
            ? filterSearch(projects).length
            : projects.length}
        </span>
      );
    }
  }

  return (
    <div className="h-full p-4">
      <div className="h-full flex flex-col gap-4">
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
          <div className="flex flex-row gap-4">
            <ProjectSearch
              searchText={searchText}
              updateSearchText={updateSearchText}
            />
          </div>
        </div>
        {projects.length > 0 ? (
          <div className="h-full overflow-auto">
            {getPaginationResults()}
            <div className="flex flex-row flex-wrap gap-4">
              {filterAndSlice(projects)
                .sort((a, b) => (a.title > b.title ? 1 : b.title > a.title ? -1 : 0))
                .map((project) => (
                  <Link
                    key={project.id}
                    to={`/projects/${project.id}`}
                    className="block"
                  >
                    <article className="flex items-center w-96 h-36 mb-4 shadow bg-white transition hover:shadow-xl">
                      <div className="p-2"></div>

                      <div className="hidden sm:block">
                        {/* <PhotoIcon className="h-24 w-24" /> */}
                        <img
                          src={`/static/projects/${project.id}/preview_map.png`}
                          height={128}
                          width={128}
                        />
                      </div>

                      <div className="flex flex-1 flex-col justify-between">
                        <div className="border-s border-gray-900/10 p-4 sm:border-l-transparent sm:p-6">
                          <h3 className="font-bold uppercase text-gray-900">
                            {project.title}
                          </h3>
                          <p className="mt-2 line-clamp-3 text-sm/relaxed text-gray-700">
                            {project.description}
                          </p>
                        </div>
                      </div>
                    </article>
                  </Link>
                ))}
            </div>
            <Pagination
              currentPage={currentPage}
              totalPages={TOTAL_PAGES}
              updateCurrentPage={updateCurrentPage}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
