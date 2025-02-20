import { useMemo, useState } from 'react';

import { Status } from '../../../Alert';
import ExtensionList, { Extension } from './ExtensionList';
import Pagination from '../../../Pagination';
import SearchBar from '../SearchBar';
import { User } from '../../../../AuthContext';

import { sorter } from '../../../utils';

type UserExtensionsProps = {
  extensions: Extension[];
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
  users: User[];
};

export default function UserExtensions({
  extensions,
  setStatus,
  users,
}: UserExtensionsProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [searchTerm, setSearchTerm] = useState<string>('');

  const updateSearchTerm = (newSearchTerm: string): void =>
    setSearchTerm(newSearchTerm);

  const filteredUsers = useMemo(() => {
    // If searchTerm is empty, return all users
    if (searchTerm === '') {
      return users
        .slice()
        .sort((a, b) =>
          sorter(a.last_name.toLowerCase(), b.last_name.toLowerCase())
        );
    }

    const lowerSearchTerm = searchTerm.toLowerCase();

    return users
      .filter(
        (user) =>
          user.first_name.toLowerCase().includes(lowerSearchTerm) ||
          user.last_name.toLowerCase().includes(lowerSearchTerm) ||
          user.email.toLowerCase().includes(searchTerm)
      )
      .sort((a, b) =>
        sorter(a.last_name.toLowerCase(), b.last_name.toLowerCase())
      );
  }, [searchTerm, users]);

  const MAX_ITEMS = 10; // max number of users per page
  const TOTAL_PAGES = Math.ceil(filteredUsers.length / MAX_ITEMS);

  /**
   * Updates the current selected pagination page.
   * @param newPage Index of new page.
   */
  function updateCurrentPage(newPage: number): void {
    const total_pages = Math.ceil(
      filteredUsers ? filteredUsers.length : 0 / MAX_ITEMS
    );

    if (newPage + 1 > total_pages) {
      setCurrentPage(total_pages - 1);
    } else if (newPage < 0) {
      setCurrentPage(0);
    } else {
      setCurrentPage(newPage);
    }
  }

  /**
   * Filters users or teams by search text and limits to current page.
   * @param items Users or teams to filter.
   * @returns
   */
  function filterAndSlice(items: User[]) {
    return items.slice(
      currentPage * MAX_ITEMS,
      MAX_ITEMS + currentPage * MAX_ITEMS
    );
  }

  /**
   * Returns available users or teams on page limitations.
   * @param items Users or teams to filter, limit, and sort.
   * @returns Array of filtered users or teams.
   */
  function getAvailableUsers(items: User[]): User[] {
    return filterAndSlice(items);
  }

  return (
    <div className="max-h-[60vh] flex flex-col gap-4">
      <h2>Users</h2>
      <SearchBar searchTerm={searchTerm} updateSearchTerm={updateSearchTerm} />
      <table className="relative w-full border-separate border-spacing-y-1 border-spacing-x-1">
        <thead>
          <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
            <th className="w-1/3">Name</th>
            <th className="w-1/3">Email</th>
            <th className="w-1/3">Extensions</th>
          </tr>
        </thead>
      </table>
      <div className="max-h-96 overflow-y-auto">
        <table className="relative w-full border-separate border-spacing-y-1 border-spacing-x-1">
          <tbody>
            {getAvailableUsers(filteredUsers).map((user) => (
              <tr key={user.id} className="text-center">
                <td className="w-1/3 p-1.5 bg-white">
                  {user.first_name} {user.last_name}
                </td>
                <td className="w-1/3 p-1.5 bg-white">{user.email}</td>
                <td className="w-1/3 p-1.5 bg-white">
                  <ExtensionList
                    extensions={extensions}
                    selectedExtensions={user.exts}
                    setStatus={setStatus}
                    userId={user.id}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination
        currentPage={currentPage}
        updateCurrentPage={updateCurrentPage}
        totalPages={TOTAL_PAGES}
      />
    </div>
  );
}
