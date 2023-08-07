import axios from 'axios';
import { Link, Outlet, useLoaderData, useParams } from 'react-router-dom';
import { BellIcon, PlusSmallIcon } from '@heroicons/react/24/outline';

interface Team {
  id: string;
  title: string;
  description: string;
}

function classNames(...classes: [string, string]) {
  return classes.filter(Boolean).join(' ');
}

export async function loader() {
  const response = await axios.get('/api/v1/teams/');
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

export default function SidebarPage() {
  const teams = useLoaderData() as Team[];
  const notifications = [{}, {}, {}, {}]; // fetch from data loader
  const { teamId } = useParams();

  return (
    <div className="flex">
      {/* sidebar */}
      <div className="flex h-screen w-80 flex-col justify-between border-e accent3">
        <div className="px-4 py-6">
          {/* notifications */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              className="relative rounded-full accent3 p-1 text-gray-600 hover:text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800"
            >
              <span className="absolute -inset-1.5" />
              <span className="sr-only">View notifications</span>
              <BellIcon className="h-6 w-6" aria-hidden="true" />
            </button>
            <span>Notifications</span>
            <div className="flex items-center justify-center h-6 w-6 rounded-full border-2 border-gray-600 text-center">
              <span className="text-sm">{notifications.length}</span>
            </div>
          </div>
          <hr className="mt-4 border-gray-700" />
          <div className="mt-6">
            <h2>My Teams</h2>
            <ul className="mt-2 space-y-1">
              {teams.map((team) => (
                <li key={team.id}>
                  <Link
                    to={`/teams/${team.id}`}
                    className={classNames(
                      teamId === team.id
                        ? 'font-semibold text-gray-700'
                        : 'font-medium text-gray-500',
                      'block rounded-lg px-4 py-2 text-sm hover:bg-gray-100 hover:text-gray-700'
                    )}
                  >
                    {team.title}
                  </Link>
                </li>
              ))}
              <li key="create-team">
                <Link
                  className="flex items-center font-medium text-gray-500 block rounded-lg px-4 py-2 text-sm hover:bg-gray-100 hover:text-gray-700"
                  to={'/teams/create'}
                >
                  <div>
                    <PlusSmallIcon className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <div>Add Team</div>
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
      {/* page content */}
      <div className="m-4">
        <Outlet />
      </div>
    </div>
  );
}
