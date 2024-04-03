import axios from 'axios';
import { useEffect, useState } from 'react';
import { useLoaderData, Link } from 'react-router-dom';

import { Button } from '../../Buttons';
import Modal from '../../Modal';
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

  function updateSearchText(query: string) {
    setSearchText(query);
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
