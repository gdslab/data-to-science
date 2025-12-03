import { isAxiosError } from 'axios';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PaperAirplaneIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconOutline } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

import CountBadge from '../../CountBadge';
import { GridIcon } from './GridIcon';
import { Project } from './ProjectList';

import api from '../../../api';
import { getCategory } from '../../maps/utils';

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
      className="block h-40"
    >
      <article
        className="relative flex items-center w-96 h-40 shadow-sm bg-white transition hover:shadow-xl"
        title={project.title}
      >
        <div className="absolute top-2 right-2">
          <button
            type="button"
            className="focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-full"
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
        <div className="w-32 h-full p-1.5 hidden sm:block bg-gray-100 relative">
          <div className="absolute inset-0 flex items-center justify-center">
            <img
              className="h-full w-full object-cover"
              src={`/static/projects/${project.id}/preview_map.png`}
              alt="Preview not available"
              onError={(e) => {
                // If the image fails to load, display a placeholder icon
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const parent = target.parentElement;
                if (parent) {
                  const icon = document.createElement('div');
                  icon.className =
                    'flex items-center justify-center w-full h-full';
                  icon.innerHTML =
                    '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 text-gray-400"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" /></svg>';
                  parent.appendChild(icon);
                }
              }}
            />
          </div>
        </div>

        <div className="w-full md:w-64 border-s border-gray-900/10 p-2 sm:border-l-transparent sm:p-4 flex flex-col h-full">
          <div>
            <h3 className="font-bold uppercase text-gray-900 max-w-48 truncate">
              {project.title}
            </h3>
            <p className="line-clamp-2 text-sm/relaxed text-gray-700 text-wrap truncate">
              {project.description}
            </p>
          </div>
          <div className="mt-auto flex items-center justify-between">
            <div className="flex flex-col items-start gap-1">
              <CountBadge
                count={project.flight_count}
                color="sky"
                label="Flights"
                icon={<PaperAirplaneIcon className="h-4 w-4 -ms-1 me-1.5" />}
                rank={getCategory(project.flight_count, 'flight')}
              />
              {project.team ? (
                <span
                  className="inline-flex items-center justify-center rounded-full px-2.5 py-0.5 bg-indigo-50 text-indigo-700"
                  title={project.team.title}
                >
                  <UserGroupIcon className="h-4 w-4 -ms-1 me-1.5" />
                  <p className="whitespace-nowrap text-xs">Team</p>
                </span>
              ) : null}
            </div>
            <CountBadge
              count={project.data_product_count}
              color="green"
              label="Data"
              icon={<GridIcon className="h-4 w-4 -ms-1 me-1.5" />}
              rank={getCategory(project.data_product_count, 'data_product')}
            />
          </div>
        </div>
      </article>
    </Link>
  );
}
