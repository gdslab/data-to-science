import { Link } from 'react-router-dom';

import { Project } from './ProjectList';

export default function ProjectCard({ project }: { project: Project }) {
  return (
    <Link key={project.id} to={`/projects/${project.id}`} className="block h-36">
      <article
        className="flex items-center w-96 h-36 shadow bg-white transition hover:shadow-xl"
        title={project.title}
      >
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
  );
}
