import { Link } from 'react-router';

import { IndoorProjectAPIResponse } from './IndoorProject';

type IndoorProjectCardProps = {
  indoorProject: IndoorProjectAPIResponse;
};

export default function IndoorProjectCard({
  indoorProject,
}: IndoorProjectCardProps) {
  return (
    <Link to={`/indoor_projects/${indoorProject.id}`} className="block h-36">
      <article className="flex items-center justify-center w-96 h-36 shadow bg-white transition hover:shadow-xl">
        <div className="w-full md:w-64 border-s border-gray-900/10 p-2 sm:border-l-transparent sm:p-4">
          <h3 className="font-bold uppercase text-gray-900 truncate">
            {indoorProject.title}
          </h3>
          <p className="mt-2 line-clamp-3 text-sm/relaxed text-gray-700 text-wrap truncate">
            {indoorProject.description}
          </p>
        </div>
      </article>
    </Link>
  );
}
