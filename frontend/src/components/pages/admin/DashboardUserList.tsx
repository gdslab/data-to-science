import Papa from 'papaparse';
import { ReactNode, useState } from 'react';

import { generateRandomProfileColor } from '../auth/Profile';
import { Button } from '../../Buttons';
import Pagination from '../../Pagination';
import { User } from '../../../AuthContext';

import { downloadFile as downloadCSV } from '../workspace/projects/fieldCampaigns/utils';

const HeaderRow = ({ children }: { children?: ReactNode }) => (
  <th className="whitespace-nowrap px-4 py-2 font-medium text-sm text-gray-900">
    {children}
  </th>
);

const BodyRow = ({ children }: { children: ReactNode }) => (
  <th className="whitespace-nowrap px-4 py-2 font-medium text-sm text-gray-700">
    {children}
  </th>
);

const UserProfilePicture = ({ user }: { user: User }) =>
  user.profile_url ? (
    <img
      key={user.profile_url.split('/').slice(-1)[0].slice(0, -4)}
      className="h-8 w-8 rounded-full"
      src={user.profile_url}
    />
  ) : (
    <div
      className="flex items-center justify-center h-8 w-8 text-white text-sm rounded-full"
      style={generateRandomProfileColor(`${user.first_name} ${user.last_name}`)}
    >
      <span className="indent-[0.1em] tracking-widest">
        {user.first_name[0] + user.last_name[0]}
      </span>
    </div>
  );

export default function DashboardUserList({ users }: { users: User[] }) {
  const [currentPage, setCurrentPage] = useState(0);

  const keysToSkip = [
    'id',
    'api_access_token',
    'exts',
    'is_approved',
    'is_email_confirmed',
    'is_superuser',
    'profile_url',
  ];

  const MAX_ITEMS = 5; // max number of users per page
  const TOTAL_PAGES = Math.ceil(users.length / MAX_ITEMS);

  /**
   * Updates the current selected pagination page.
   * @param newPage Index of new page.
   */
  function updateCurrentPage(newPage: number): void {
    const total_pages = Math.ceil(users ? users.length : 0 / MAX_ITEMS);

    if (newPage + 1 > total_pages) {
      setCurrentPage(total_pages - 1);
    } else if (newPage < 0) {
      setCurrentPage(0);
    } else {
      setCurrentPage(newPage);
    }
  }

  /**
   * Filters users by search text and limits to current page.
   * @param users Users to filter.
   * @returns
   */
  function filterAndSlice(users: User[]) {
    return users.slice(currentPage * MAX_ITEMS, MAX_ITEMS + currentPage * MAX_ITEMS);
  }

  /**
   * Returns available users on page limitations.
   * @param users Users to filter, limit, and sort.
   * @returns Array of filtered users.
   */
  function getAvailableUsers(users): User[] {
    return filterAndSlice(users);
  }

  return (
    <div>
      <table className="w-full border-separate border-spacing-1">
        <thead>
          <tr className="font-semibold text-md text-slate-600">
            <HeaderRow></HeaderRow>
            <HeaderRow>Name</HeaderRow>
            <HeaderRow>Email</HeaderRow>
            <HeaderRow>Date Joined</HeaderRow>
          </tr>
        </thead>
        <tbody>
          {getAvailableUsers(users).map((user) => (
            <tr key={user.id}>
              <BodyRow>
                <UserProfilePicture user={user} />
              </BodyRow>
              <HeaderRow>
                {user.first_name} {user.last_name}
              </HeaderRow>
              <BodyRow>{user.email}</BodyRow>
              <BodyRow>{new Date(user.created_at).toLocaleDateString()}</BodyRow>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex flex-cols justify-between gap-4">
        <div></div>
        <Pagination
          currentPage={currentPage}
          updateCurrentPage={updateCurrentPage}
          totalPages={TOTAL_PAGES}
        />

        <Button
          type="button"
          size="sm"
          onClick={() => {
            const csvData = Papa.unparse(
              users.map((user) =>
                Object.fromEntries(
                  Object.entries(user).filter(([key]) => !keysToSkip.includes(key))
                )
              )
            );
            const csvFile = new Blob([csvData], { type: 'text/csv' });
            downloadCSV(csvFile, 'users.csv');
          }}
        >
          Export CSV
        </Button>
      </div>
    </div>
  );
}
