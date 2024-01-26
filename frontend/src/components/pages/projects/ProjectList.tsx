import axios from 'axios';
import { useState } from 'react';
import { useLoaderData, Link } from 'react-router-dom';

import { Button } from '../../Buttons';
import Modal from '../../Modal';
import ProjectForm from './ProjectForm';

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
  const projects = useLoaderData() as Project[];
  return (
    <div className="p-4">
      <h1>Projects</h1>
      <div className="w-96">
        <Button icon="folderplus" onClick={() => setOpen(true)}>
          Create
        </Button>
        <Modal open={open} setOpen={setOpen}>
          <ProjectForm setModalOpen={setOpen} />
        </Modal>
      </div>
      {projects.length > 0 ? (
        <div className="mt-6">
          {projects
            .sort((a, b) => (a.title > b.title ? 1 : b.title > a.title ? -1 : 0))
            .map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`} className="block">
                <article className="flex items-center mb-4 shadow bg-white transition hover:shadow-xl">
                  <div className="p-2"></div>

                  <div className="hidden sm:block sm:basis-56">
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
      ) : null}
    </div>
  );
}
