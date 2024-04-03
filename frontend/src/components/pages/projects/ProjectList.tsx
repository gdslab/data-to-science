import axios from 'axios';
import { useEffect, useState } from 'react';
import { useLoaderData, Link } from 'react-router-dom';

import { Button } from '../../Buttons';
import Modal from '../../Modal';
import ProjectForm from './ProjectForm';
import { useProjectContext } from './ProjectContext';

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
  const [open, setOpen] = useState(false);
  const [searchText, setSearchText] = useState('');
  const projects = useLoaderData() as Project[];

  const { locationDispatch, project, projectDispatch } = useProjectContext();

  useEffect(() => {
    locationDispatch({ type: 'clear', payload: null });
  }, [open]);

  useEffect(() => {
    locationDispatch({ type: 'clear', payload: null });
    projectDispatch({ type: 'clear', payload: null });
  }, [project]);

  function updateSearchText(e) {
    setSearchText(e.target.value);
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
            <div className="relative min-w-96">
              <label htmlFor="Search" className="sr-only">
                {' '}
                Search{' '}
              </label>
              <input
                type="text"
                id="Search"
                placeholder="Search for project by title or description"
                className="w-full rounded-md border-gray-200 px-4 py-2.5 pe-10 shadow sm:text-sm"
                value={searchText}
                onChange={updateSearchText}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    setSearchText('');
                  }
                }}
              />
              <span className="absolute inset-y-0 end-0 grid w-10 place-content-center">
                <span className="sr-only">Search</span>

                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                  className="h-4 w-4 text-slate-400"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                  />
                </svg>
              </span>
            </div>
          </div>
        </div>
        {projects.length > 0 ? (
          <div className="h-full overflow-auto">
            <div className="flex flex-row flex-wrap gap-4">
              {projects
                .filter(
                  (project) =>
                    !project.title ||
                    project.title.toLowerCase().includes(searchText.toLowerCase()) ||
                    project.description.toLowerCase().includes(searchText.toLowerCase())
                )
                .sort((a, b) => (a.title > b.title ? 1 : b.title > a.title ? -1 : 0))
                .map((project) => (
                  <Link
                    key={project.id}
                    to={`/projects/${project.id}`}
                    className="block"
                  >
                    <article className="flex items-center w-96 mb-4 shadow bg-white transition hover:shadow-xl">
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
          </div>
        ) : null}
      </div>
    </div>
  );
}
