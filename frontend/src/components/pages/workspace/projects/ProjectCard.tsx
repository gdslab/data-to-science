import { isAxiosError } from 'axios';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { StarIcon as StarIconOutline } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

import { Project } from './ProjectList';

import api from '../../../../api';

export default function ProjectCard({
  project,
  revalidate,
}: {
  project: Project;
  revalidate: () => void;
}) {
  const [liked, setLiked] = useState(project.liked);
  const [isLoading, setIsLoading] = useState(false);

  const handleOnBookmarkClick = async (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent link navigation
    e.stopPropagation(); // Prevent event bubbling

    if (isLoading) return;

    setIsLoading(true);
    try {
      const response = await api[liked ? 'delete' : 'post'](
        `/projects/${project.id}/like`
      );
      if (response.status === 201) {
        setLiked(!liked);
        revalidate(); // Trigger revalidation after successful bookmark toggle
      } else if (response.status === 200) {
        setLiked(!liked);
        revalidate(); // Trigger revalidation after successful bookmark toggle
      }
    } catch (error) {
      if (isAxiosError(error)) {
        console.error('Bookmark error:', error.response?.data);
      } else {
        console.error('Unexpected error:', error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Link
      key={project.id}
      to={`/projects/${project.id}`}
      className="block h-36"
    >
      <article
        className="relative flex items-center w-96 h-36 shadow bg-white transition hover:shadow-xl"
        title={project.title}
      >
        <div className="absolute top-2 right-2">
          <button
            type="button"
            className="focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-full"
            onClick={handleOnBookmarkClick}
            disabled={isLoading}
            aria-label={liked ? 'Remove bookmark' : 'Bookmark project'}
          >
            {liked ? (
              <StarIconSolid
                className={`w-6 h-6 text-amber-500 ${
                  isLoading ? 'opacity-50' : ''
                }`}
              />
            ) : (
              <StarIconOutline
                className={`w-6 h-6 text-gray-400 ${
                  isLoading ? 'opacity-50' : ''
                }`}
              />
            )}
          </button>
        </div>
        <div className="w-32 h-full p-1.5 hidden sm:block">
          <img
            className="h-full object-cover"
            src={`/static/projects/${project.id}/preview_map.png`}
            alt={`Preview map for ${project.title}`}
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = '/static/projects/default-preview.png';
            }}
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
