import clsx from 'clsx';
import { Link, useLocation } from 'react-router-dom';
import {
  CircleStackIcon,
  HomeIcon,
  MapIcon,
  PuzzlePieceIcon,
  PresentationChartBarIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';

export default function SidePanel() {
  const { pathname } = useLocation();
  const currentPage = pathname.split('/').slice(-1)[0];

  return (
    <div className="flex h-full w-16 flex-col justify-between border-e bg-white z-1000">
      <div>
        <div className="border-t border-gray-100">
          <div className="px-2">
            <div className="py-4">
              <Link
                to="/admin/dashboard"
                className={clsx(
                  't group relative flex justify-center rounded px-2 py-1.5',
                  {
                    'bg-blue-50 text-blue-700': currentPage === 'dashboard',
                    'text-gray-500 hover:bg-gray-50 hover:text-gray-700':
                      currentPage !== 'dashboard',
                  }
                )}
              >
                <HomeIcon className="h-5 w-5 opacity-75" strokeWidth={2} />

                <span className="invisible absolute start-full top-1/2 ms-4 -translate-y-1/2 rounded bg-gray-900 px-2 py-1.5 text-xs font-medium text-white group-hover:visible">
                  Site Stats
                </span>
              </Link>
            </div>

            <ul className="space-y-1 border-t border-gray-100 pt-4">
              <li>
                <Link
                  to="/admin/dashboard/users"
                  className={clsx(
                    'group relative flex justify-center rounded px-2 py-1.5',
                    {
                      'bg-blue-50 text-blue-700': currentPage === 'users',
                      'text-gray-500 hover:bg-gray-50 hover:text-gray-700':
                        currentPage !== 'users',
                    }
                  )}
                >
                  <UsersIcon className="h-5 w-5 opacity-75" strokeWidth={2} />

                  <span className="invisible absolute start-full top-1/2 ms-4 -translate-y-1/2 rounded bg-gray-900 px-2 py-1.5 text-xs font-medium text-white group-hover:visible">
                    Users
                  </span>
                </Link>
              </li>

              <li>
                <Link
                  to="/admin/dashboard/map"
                  className={clsx(
                    'group relative flex justify-center rounded px-2 py-1.5',
                    {
                      'bg-blue-50 text-blue-700': currentPage === 'map',
                      'text-gray-500 hover:bg-gray-50 hover:text-gray-700':
                        currentPage !== 'map',
                    }
                  )}
                >
                  <MapIcon className="h-5 w-5 opacity-75" strokeWidth={2} />

                  <span className="invisible absolute start-full top-1/2 ms-4 -translate-y-1/2 rounded bg-gray-900 px-2 py-1.5 text-xs font-medium text-white group-hover:visible">
                    Projects Map
                  </span>
                </Link>
              </li>

              <li>
                <Link
                  to="/admin/dashboard/extensions"
                  className={clsx(
                    'group relative flex justify-center rounded px-2 py-1.5',
                    {
                      'bg-blue-50 text-blue-700': currentPage === 'extensions',
                      'text-gray-500 hover:bg-gray-50 hover:text-gray-700':
                        currentPage !== 'extensions',
                    }
                  )}
                >
                  <PuzzlePieceIcon className="h-5 w-5 opacity-75" strokeWidth={2} />

                  <span className="invisible absolute start-full top-1/2 ms-4 -translate-y-1/2 rounded bg-gray-900 px-2 py-1.5 text-xs font-medium text-white group-hover:visible">
                    Manage Extensions
                  </span>
                </Link>
              </li>

              <li>
                <Link
                  to="/admin/dashboard/storage"
                  className={clsx(
                    'group relative flex justify-center rounded px-2 py-1.5',
                    {
                      'bg-blue-50 text-blue-700': currentPage === 'storage',
                      'text-gray-500 hover:bg-gray-50 hover:text-gray-700':
                        currentPage !== 'storage',
                    }
                  )}
                >
                  <CircleStackIcon className="h-5 w-5 opacity-75" strokeWidth={2} />

                  <span className="invisible absolute start-full top-1/2 ms-4 -translate-y-1/2 rounded bg-gray-900 px-2 py-1.5 text-xs font-medium text-white group-hover:visible">
                    Project Storage
                  </span>
                </Link>
              </li>

              <li>
                <Link
                  to="/admin/dashboard/charts"
                  className={clsx(
                    'group relative flex justify-center rounded px-2 py-1.5',
                    {
                      'bg-blue-50 text-blue-700': currentPage === 'charts',
                      'text-gray-500 hover:bg-gray-50 hover:text-gray-700':
                        currentPage !== 'charts',
                    }
                  )}
                >
                  <PresentationChartBarIcon
                    className="h-5 w-5 opacity-75"
                    strokeWidth={2}
                  />

                  <span className="invisible absolute start-full top-1/2 ms-4 -translate-y-1/2 rounded bg-gray-900 px-2 py-1.5 text-xs font-medium text-white group-hover:visible">
                    Charts
                  </span>
                </Link>
              </li>

              {/* <li>
                <a
                  href="#"
                  className="group relative flex justify-center rounded px-2 py-1.5 text-gray-500 hover:bg-gray-50 hover:text-gray-700"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="size-5 opacity-75"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                    />
                  </svg>

                  <span className="invisible absolute start-full top-1/2 ms-4 -translate-y-1/2 rounded bg-gray-900 px-2 py-1.5 text-xs font-medium text-white group-hover:visible">
                    Invoices
                  </span>
                </a>
              </li>

              <li>
                <a
                  href="#"
                  className="group relative flex justify-center rounded px-2 py-1.5 text-gray-500 hover:bg-gray-50 hover:text-gray-700"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="size-5 opacity-75"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>

                  <span className="invisible absolute start-full top-1/2 ms-4 -translate-y-1/2 rounded bg-gray-900 px-2 py-1.5 text-xs font-medium text-white group-hover:visible">
                    Account
                  </span>
                </a>
              </li> */}
            </ul>
          </div>
        </div>
      </div>

      <div className="sticky inset-x-0 bottom-0 border-t border-gray-100 bg-white p-2">
        <Link
          to="/auth/logout"
          className="group relative flex w-full justify-center rounded-lg px-2 py-1.5 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="size-5 opacity-75"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
          </svg>

          <span className="invisible absolute start-full top-1/2 ms-4 -translate-y-1/2 rounded bg-gray-900 px-2 py-1.5 text-xs font-medium text-white group-hover:visible">
            Sign out
          </span>
        </Link>
      </div>
    </div>
  );
}
