import axios, { AxiosResponse } from 'axios';
import { Params, useLoaderData } from 'react-router-dom';

import { IndoorProjectAPIResponse } from './IndoorProject';
import IndoorProjectUploadModal from './IndoorProjectUploadModal';
import { Project } from '../ProjectList';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const indoorProjectResponse: AxiosResponse<IndoorProjectAPIResponse> =
      await axios.get(
        `${import.meta.env.VITE_API_V1_STR}/indoor_projects/${params.indoorProjectId}`
      );
    const projectsResponse: AxiosResponse<Project[]> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects`
    );
    if (indoorProjectResponse && indoorProjectResponse.status == 200) {
      if (projectsResponse && projectsResponse.status == 200) {
        return {
          indoorProject: indoorProjectResponse.data,
          projects: projectsResponse.data,
        };
      } else {
        return {
          indoorProject: indoorProjectResponse.data,
          projects: [],
        };
      }
    } else {
      throw new Response('Indoor project not found', { status: 404 });
    }
  } catch (err) {
    throw new Response('Indoor project not found', { status: 404 });
  }
}

export default function IndoorProjectDetail() {
  const { indoorProject, projects } = useLoaderData() as {
    indoorProject: IndoorProjectAPIResponse;
    projects: Project[];
  };
  if (!indoorProject)
    return (
      <div>
        <span>No indoor project found</span>
      </div>
    );

  return (
    <div className="mx-4 my-2">
      JSON Response:
      <pre className="whitespace-pre-wrap p-10 border-2 border-slate-600">
        {JSON.stringify(indoorProject, null, 2)}
      </pre>
      <IndoorProjectUploadModal indoorProjectId={indoorProject.id} />
      {projects.length > 0 && (
        <div>
          <label className="block" htmlFor="projectSelect">
            Associate with project
          </label>
          <select name="projectSelect">
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.title}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
