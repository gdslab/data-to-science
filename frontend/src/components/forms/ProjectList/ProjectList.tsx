import axios from 'axios';
import { useLoaderData, Link } from 'react-router-dom';

import { CustomButton } from '../CustomButtons';

interface Project {
  id: string;
  title: string;
  description: string;
}

export async function loader() {
  const response = await axios.get('/api/v1/projects/');
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

export default function ProjectList() {
  const projects = useLoaderData() as Project[];
  console.log(projects);
  return (
    <div className="m-4">
      <h1>Projects</h1>
      <div className="w-48">
        <Link to="/projects/create">
          <CustomButton aria-label="Add new project">Add new project</CustomButton>
        </Link>
      </div>
      {projects.length > 0 ? (
        <div className="mt-6">
          {projects.map((project) => (
            <article
              key={project.id}
              className="flex mb-4 bg-white transition hover:shadow-xl"
            >
              <div className="rotate-180 p-2 [writing-mode:_vertical-lr]">
                <time
                  dateTime="2022-10-10"
                  className="flex items-center justify-between gap-4 text-xs font-bold uppercase text-gray-900"
                >
                  <span>2022</span>
                  <span className="w-px flex-1 bg-gray-900/10"></span>
                  <span>Oct 10</span>
                </time>
              </div>

              <div className="hidden sm:block sm:basis-56">
                <img
                  alt="Guitar"
                  src="https://images.unsplash.com/photo-1609557927087-f9cf8e88de18?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1740&q=80"
                  className="aspect-square h-full w-full object-cover"
                />
              </div>

              <div className="flex flex-1 flex-col justify-between">
                <div className="border-s border-gray-900/10 p-4 sm:border-l-transparent sm:p-6">
                  <a href="#">
                    <h3 className="font-bold uppercase text-gray-900">
                      {project.title}
                    </h3>
                  </a>

                  <p className="mt-2 line-clamp-3 text-sm/relaxed text-gray-700">
                    {project.description}
                  </p>
                </div>

                <div className="sm:flex sm:items-end sm:justify-end">
                  <Link
                    to={`/projects/${project.id}`}
                    className="block bg-warning px-5 py-3 text-center text-xs font-bold uppercase text-gray-900 transition hover:bg-yellow-400"
                  >
                    Open project
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <em>No active projects</em>
      )}
    </div>
  );
}
