import axios from 'axios';
import { useEffect } from 'react';
import {
  Link,
  Outlet,
  useLoaderData,
  useLocation,
  useParams,
  useRevalidator,
} from 'react-router-dom';
import { PlusCircleIcon, UserGroupIcon } from '@heroicons/react/24/outline';

import { classNames } from '../../utils';

export interface Team {
  id: string;
  is_owner: boolean;
  title: string;
  description: string;
}

export async function loader() {
  const response = await axios.get('/api/v1/teams');
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

export default function SidebarPage() {
  const teams = useLoaderData() as Team[];
  const { teamId } = useParams();
  const location = useLocation();
  const revalidator = useRevalidator();

  useEffect(() => {
    if (location.state && location.state.reload) {
      revalidator.revalidate();
    }
  }, [location.state]);

  return (
    <div className="flex">
      {/* sidebar */}
      <div className="flex h-screen w-80 flex-col justify-between border-e bg-accent3 text-slate-200">
        <div className="px-4 py-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Link
                className="relative rounded-full p-1 text-accent1 visited:text-accent1 hover:text-slate-50 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800"
                to="/teams/create"
              >
                <span className="absolute -inset-1.5" />
                <span className="sr-only">Add a New Team</span>
                <PlusCircleIcon className="h-6 w-6" aria-hidden="true" />
              </Link>
              <span className="ml-4">Add a New Team</span>
            </div>
          </div>
          <hr className="mb-8 border-gray-300" />
          <div>
            <div className="flex items-center mb-4">
              <div className="relative rounded-full accent3 p-1 hover:text-slate-50 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800">
                <span className="absolute -inset-1.5" />
                <span className="sr-only">Team List</span>
                <UserGroupIcon className="h-6 w-6" aria-hidden="true" />
              </div>
              <span className="ml-4">Team List</span>
            </div>
            <ul className="space-y-1">
              {teams.map((team) => (
                <li key={team.id}>
                  <Link
                    to={`/teams/${team.id}`}
                    className={classNames(
                      teamId === team.id ? 'font-semibold text-slate-50' : '',
                      'block rounded-lg px-4 py-2 text-sm hover:bg-gray-100 hover:text-gray-700'
                    )}
                  >
                    {team.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
      {/* page content */}
      <div className="m-4 w-full">
        {location.pathname === '/teams' && teams.length < 1 ? (
          <span>
            You do not currently belong to any teams. Use the{' '}
            <strong className="font-bold">Add a New Team</strong> button in the side
            menu to create your first team.
          </span>
        ) : null}
        <Outlet />
      </div>
    </div>
  );
}
