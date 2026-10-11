import { useMemo, useState } from 'react';

import { Status } from '../../../Alert';
import { DataCard } from '../DataCards';
import ExtensionList, { Extension } from './ExtensionList';
import Pagination from '../../../Pagination';
import SearchBar from '../SearchBar';
import { User } from '../../../../AuthContext';

import { usePaginatedList } from '../../../hooks';
import { sorter } from '../../../utils';

const MAX_ITEMS = 10; // max number of users per page

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
          user.email.toLowerCase().includes(lowerSearchTerm)
      )
      .sort((a, b) =>
        sorter(a.last_name.toLowerCase(), b.last_name.toLowerCase())
      );
  }, [searchTerm, users]);

  const { pageItems, totalPages, currentPage, updateCurrentPage } =
    usePaginatedList(filteredUsers, MAX_ITEMS);

  return (
    <div className="max-h-[60vh] flex flex-col gap-4">
      <h2>Users</h2>
      <SearchBar
        searchTerm={searchTerm}
        updateSearchTerm={updateSearchTerm}
        placeholder="Search by name or email"
      />

      {filteredUsers.length === 0 ? (
        <p className="text-gray-500">No users match your search.</p>
      ) : (
        <>
          {/* Header and body live in one table so the columns stay aligned; the
              sticky header pins to the top of the shared scroll container. */}
          <div className="hidden max-h-96 overflow-y-auto md:block">
            <table className="relative w-full border-separate border-spacing-y-1 border-spacing-x-1">
              <thead>
                <tr className="h-12 text-slate-700">
                  <th className="sticky top-0 z-10 w-1/3 bg-slate-300">Name</th>
                  <th className="sticky top-0 z-10 w-1/3 bg-slate-300">
                    Email
                  </th>
                  <th className="sticky top-0 z-10 w-1/3 bg-slate-300">
                    Extensions
                  </th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((user) => (
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

          {/* Three columns plus a checkbox row cannot fit a phone, so the same
              rows render as cards below `md`. */}
          <div className="flex flex-col gap-3 md:hidden">
            {pageItems.map((user) => (
              <DataCard
                key={user.id}
                title={`${user.first_name} ${user.last_name}`}
                subtitle={user.email}
              >
                <div className="mt-3">
                  <ExtensionList
                    extensions={extensions}
                    selectedExtensions={user.exts}
                    setStatus={setStatus}
                    userId={user.id}
                  />
                </div>
              </DataCard>
            ))}
          </div>

          <Pagination
            currentPage={currentPage}
            updateCurrentPage={updateCurrentPage}
            totalPages={totalPages}
          />
        </>
      )}
    </div>
  );
}
