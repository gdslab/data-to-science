import Papa from 'papaparse';
import { useContext, useMemo, useState } from 'react';

import { generateRandomProfileColor } from '../auth/Profile';
import { Button } from '../../Buttons';
import Pagination from '../../Pagination';
import AuthContext, { User } from '../../../AuthContext';
import { confirm } from '../../ConfirmationDialog';
import api from '../../../api';

import { downloadFile as downloadCSV } from '../projects/fieldCampaigns/utils';

const UserProfilePicture = ({ user }: { user: User }) =>
  user.profile_url ? (
    <div className="w-full flex items-center justify-center">
      <img
        key={user.profile_url.split('/').slice(-1)[0].slice(0, -4)}
        className="h-8 w-8 rounded-full"
        src={user.profile_url}
      />
    </div>
  ) : (
    <div className="w-full flex items-center justify-center">
      <div
        className="flex items-center justify-center h-8 w-8 text-white text-sm rounded-full"
        style={generateRandomProfileColor(
          `${user.first_name} ${user.last_name}`
        )}
      >
        <span className="indent-[0.1em] tracking-widest">
          {user.first_name[0] + user.last_name[0]}
        </span>
      </div>
    </div>
  );

type SortColumn = 'name' | 'email' | 'created_at' | 'last_login_at' | 'last_activity_at' | 'is_approved';
type SortDirection = 'asc' | 'desc';

export default function DashboardUserList({
  users,
  setUsers,
}: {
  users: User[];
  setUsers: (users: User[] | ((prevUsers: User[]) => User[])) => void;
}) {
  const { user: currentUser } = useContext(AuthContext);
  const [currentPage, setCurrentPage] = useState(0);
  const [sortColumn, setSortColumn] = useState<SortColumn>('created_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [loadingUserId, setLoadingUserId] = useState<string | null>(null);

  const keysToSkip = [
    'id',
    'api_access_token',
    'exts',
    'is_approved',
    'is_email_confirmed',
    'is_superuser',
    'profile_url',
    'last_login_at',
    'last_activity_at',
  ];

  const MAX_ITEMS = 10; // max number of users per page
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
   * Handle column header click to toggle sorting
   */
  function handleSort(column: SortColumn) {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  }

  /**
   * Handle approval toggle
   */
  async function handleApprovalToggle(user: User) {
    const action = user.is_approved ? 'revoke approval for' : 'approve';
    const confirmed = await confirm({
      title: 'Confirm Action',
      description: `Are you sure you want to ${action} <strong>${user.first_name} ${user.last_name}</strong>?`,
      confirmation: '',
    });

    if (confirmed) {
      setLoadingUserId(user.id);
      try {
        await api.patch(`/admin/users/${user.id}/approval`, {
          is_approved: !user.is_approved,
        });
        // Update parent state - use callback to update the full user list
        setUsers((prevUsers) =>
          prevUsers.map((u) =>
            u.id === user.id ? { ...u, is_approved: !u.is_approved } : u
          )
        );
      } catch (error) {
        console.error('Failed to update approval status:', error);
        alert('Failed to update approval status. Please try again.');
      } finally {
        setLoadingUserId(null);
      }
    }
  }

  /**
   * Sort and paginate users
   */
  const sortedAndPaginatedUsers = useMemo(() => {
    const sorted = [...users].sort((a, b) => {
      let comparison = 0;

      switch (sortColumn) {
        case 'name':
          comparison = `${a.last_name.trim()} ${a.first_name.trim()}`
            .toLowerCase()
            .localeCompare(`${b.last_name.trim()} ${b.first_name.trim()}`.toLowerCase());
          break;
        case 'email':
          comparison = a.email.toLowerCase().localeCompare(b.email.toLowerCase());
          break;
        case 'created_at':
          comparison =
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'last_login_at':
          // Handle null values - always put them at the end regardless of sort direction
          if (a.last_login_at === null && b.last_login_at === null) {
            comparison = 0;
          } else if (a.last_login_at === null) {
            // a is null, so it should go after b (return positive to sort a after b)
            comparison = sortDirection === 'asc' ? 1 : -1;
          } else if (b.last_login_at === null) {
            // b is null, so it should go after a (return negative to sort a before b)
            comparison = sortDirection === 'asc' ? -1 : 1;
          } else {
            comparison = new Date(a.last_login_at).getTime() - new Date(b.last_login_at).getTime();
          }
          break;
        case 'last_activity_at':
          // Handle null values - always put them at the end regardless of sort direction
          if (a.last_activity_at === null && b.last_activity_at === null) {
            comparison = 0;
          } else if (a.last_activity_at === null) {
            // a is null, so it should go after b (return positive to sort a after b)
            comparison = sortDirection === 'asc' ? 1 : -1;
          } else if (b.last_activity_at === null) {
            // b is null, so it should go after a (return negative to sort a before b)
            comparison = sortDirection === 'asc' ? -1 : 1;
          } else {
            comparison = new Date(a.last_activity_at).getTime() - new Date(b.last_activity_at).getTime();
          }
          break;
        case 'is_approved':
          comparison = Number(b.is_approved) - Number(a.is_approved);
          break;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return sorted.slice(
      currentPage * MAX_ITEMS,
      MAX_ITEMS + currentPage * MAX_ITEMS
    );
  }, [users, sortColumn, sortDirection, currentPage]);

  /**
   * Render sort indicator
   */
  function SortIndicator({ column }: { column: SortColumn }) {
    if (sortColumn !== column) {
      return <span className="ml-1 text-gray-400">↕</span>;
    }
    return (
      <span className="ml-1">
        {sortDirection === 'asc' ? '↑' : '↓'}
      </span>
    );
  }

  return (
    <div className="max-h-[40vh] w-full flex flex-col gap-4">
      <div className="md:max-h-96 max-h-60 overflow-y-auto overflow-x-auto">
        <table className="relative w-full min-w-[1200px] border-collapse">
          <thead>
            <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300 z-10">
              <th
                className="cursor-pointer hover:bg-slate-400 transition whitespace-nowrap px-2 bg-slate-300 border-b-2 border-slate-400"
                style={{ width: '180px' }}
                onClick={() => handleSort('name')}
              >
                Name
                <SortIndicator column="name" />
              </th>
              <th
                className="cursor-pointer hover:bg-slate-400 transition whitespace-nowrap px-2 bg-slate-300 border-b-2 border-slate-400"
                style={{ width: '200px' }}
                onClick={() => handleSort('email')}
              >
                Email
                <SortIndicator column="email" />
              </th>
              <th
                className="cursor-pointer hover:bg-slate-400 transition whitespace-nowrap px-2 bg-slate-300 border-b-2 border-slate-400"
                style={{ width: '120px' }}
                onClick={() => handleSort('created_at')}
              >
                Date Joined
                <SortIndicator column="created_at" />
              </th>
              <th
                className="cursor-pointer hover:bg-slate-400 transition whitespace-nowrap px-2 bg-slate-300 border-b-2 border-slate-400"
                style={{ width: '180px' }}
                onClick={() => handleSort('last_login_at')}
              >
                Last Login
                <SortIndicator column="last_login_at" />
              </th>
              <th
                className="cursor-pointer hover:bg-slate-400 transition whitespace-nowrap px-2 bg-slate-300 border-b-2 border-slate-400"
                style={{ width: '180px' }}
                onClick={() => handleSort('last_activity_at')}
              >
                Last Activity
                <SortIndicator column="last_activity_at" />
              </th>
              {currentUser?.is_superuser && (
                <th
                  className="cursor-pointer hover:bg-slate-400 transition whitespace-nowrap px-2 bg-slate-300 border-b-2 border-slate-400"
                  style={{ width: '140px' }}
                  onClick={() => handleSort('is_approved')}
                >
                  Approval
                  <SortIndicator column="is_approved" />
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {sortedAndPaginatedUsers.map((user) => (
              <tr key={user.id} className="text-center border-b border-gray-200">
                <td className="p-1.5 bg-white" style={{ width: '180px' }}>
                  <div className="flex items-center gap-2 justify-center">
                    <div className="shrink-0">
                      <UserProfilePicture user={user} />
                    </div>
                    <span className="truncate">
                      {user.first_name} {user.last_name}
                    </span>
                  </div>
                </td>
                <td className="p-1.5 bg-white truncate" style={{ width: '200px' }}>
                  {user.email}
                </td>
                <td className="p-1.5 bg-white whitespace-nowrap text-sm" style={{ width: '120px' }}>
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
                <td className="p-1.5 bg-white whitespace-nowrap text-sm" style={{ width: '180px' }}>
                  {user.last_login_at
                    ? new Date(user.last_login_at).toLocaleString()
                    : '-'}
                </td>
                <td className="p-1.5 bg-white whitespace-nowrap text-sm" style={{ width: '180px' }}>
                  {user.last_activity_at
                    ? new Date(user.last_activity_at).toLocaleString()
                    : '-'}
                </td>
                {currentUser?.is_superuser && (
                  <td className="p-1.5 bg-white" style={{ width: '140px' }}>
                    <div className="flex items-center justify-center gap-2">
                      <span
                        className={`text-lg ${user.is_approved ? 'text-green-600' : 'text-red-600'}`}
                      >
                        {user.is_approved ? '✓' : '✗'}
                      </span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={user.is_approved}
                          onChange={() => handleApprovalToggle(user)}
                          disabled={loadingUserId === user.id}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-hidden peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                      {loadingUserId === user.id && (
                        <span className="text-sm text-gray-500">...</span>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
                  Object.entries(user).filter(
                    ([key]) => !keysToSkip.includes(key)
                  )
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
