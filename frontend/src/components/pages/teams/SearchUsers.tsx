import { useState } from 'react';

import { User } from '../../../AuthContext';
import { generateRandomProfileColor } from '../auth/Profile';
import { TeamMember } from './TeamDetail';
import { ProjectMember } from '../projects/ProjectAccess';

import api from '../../../api';
import { sorter } from '../../utils';

export interface UserSearch extends User {
  checked: boolean;
}

function SearchUsersBar({
  setSearchResults,
  user,
}: {
  setSearchResults: React.Dispatch<React.SetStateAction<UserSearch[]>>;
  user: User | null;
}) {
  const [searchValue, setSearchValue] = useState('');

  function updateSearchValue(e) {
    setSearchValue(e.target.value);
  }

  async function searchUsers() {
    try {
      const response = await api.get('/users', { params: { q: searchValue } });
      if (response) {
        const users = response.data
          .filter((u) => u.id !== user?.id)
          .map((u) => ({ ...u, checked: false }));
        setSearchResults(users);
      }
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="relative">
      <label htmlFor="Search" className="sr-only">
        {' '}
        Search{' '}
      </label>

      <input
        type="text"
        id="Search"
        placeholder="Search for users by name"
        className="w-full rounded-md border-gray-200 px-4 py-2.5 pe-10 shadow-sm sm:text-sm"
        value={searchValue}
        onChange={updateSearchValue}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            searchUsers();
            setSearchValue('');
          }
        }}
      />

      <span className="absolute inset-y-0 end-0 grid w-10 place-content-center">
        <button
          type="button"
          className="text-gray-600 hover:text-gray-700"
          onClick={() => {
            searchUsers();
            setSearchValue('');
          }}
        >
          <span className="sr-only">Search</span>

          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="1.5"
            stroke="currentColor"
            className="h-4 w-4"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
            />
          </svg>
        </button>
      </span>
    </div>
  );
}

interface SearchUsersResults {
  currentMembers: UserSearch[] | TeamMember[] | ProjectMember[];
  searchResults: UserSearch[];
  setSearchResults: React.Dispatch<React.SetStateAction<UserSearch[]>>;
}

function SearchUsersResults({
  currentMembers,
  searchResults,
  setSearchResults,
}: SearchUsersResults) {
  if (searchResults && searchResults.length > 0) {
    return (
      <div className="grid grid-flow-row gap-4">
        <span className="text-slate-600 font-bold text-sm sm:text-base">
          Search Results
        </span>
        <div className="max-h-[40vh] overflow-y-auto overflow-x-auto border border-gray-200 rounded-lg shadow-xs">
          <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-xs sm:text-sm">
            <thead className="text-left sticky top-0 z-10 bg-white border-b-2 border-gray-200">
              <tr>
                <th className="whitespace-nowrap px-2 sm:px-4 py-2 font-medium text-gray-900">
                  Name
                </th>
                <th className="text-center px-2 sm:px-4 py-2">
                  <span
                    className="text-sky-600 hover:text-sky-800 cursor-pointer text-xs sm:text-sm"
                    onClick={() => {
                      const updatedSearchResults = searchResults.map((user) => {
                        return {
                          ...user,
                          checked:
                            currentMembers
                              .map((currentMember) => currentMember.email)
                              .indexOf(user.email) < 0,
                        };
                      });
                      setSearchResults(updatedSearchResults);
                    }}
                  >
                    Select All
                  </span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {searchResults
                .sort((a, b) => sorter(a.first_name, b.first_name))
                .map((user) => (
                  <tr key={user.id} className="odd:bg-gray-50">
                    <td className="flex items-center justify-start gap-2 sm:gap-4 whitespace-nowrap px-2 sm:px-4 py-2 font-medium text-gray-900">
                      {user.profile_url ? (
                        <img
                          key={user.profile_url
                            .split('/')
                            .slice(-1)[0]
                            .slice(0, -4)}
                          className="h-6 w-6 sm:h-8 sm:w-8 rounded-full shrink-0"
                          src={user.profile_url}
                        />
                      ) : (
                        <div
                          className="flex items-center justify-center h-6 w-6 sm:h-8 sm:w-8 gap-1 text-white text-xs sm:text-sm rounded-full shrink-0"
                          style={generateRandomProfileColor(
                            user.first_name + ' ' + user.last_name
                          )}
                        >
                          <span className="indent-[0.1em] tracking-widest">
                            {user.first_name[0] + user.last_name[0]}
                          </span>
                        </div>
                      )}
                      <span className="truncate">{`${user.first_name} ${user.last_name}`}</span>
                    </td>
                    <td className="text-center px-2 sm:px-4 py-2">
                      {currentMembers.filter(
                        ({ email }) => email === user.email
                      ).length > 0 ? (
                        <span className="italic text-slate-700 text-xs sm:text-sm">
                          Already member
                        </span>
                      ) : (
                        <label
                          htmlFor={`${user.id}-search-checkbox`}
                          className="relative h-8 w-14 cursor-pointer inline-flex items-center justify-center"
                        >
                          <input
                            id={`${user.id}-search-checkbox`}
                            type="checkbox"
                            value={user.id}
                            checked={user.checked}
                            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded-sm focus:ring-blue-500 focus:ring-2 touch-manipulation"
                            onChange={(e) => {
                              const updatedSearchResults = searchResults.map(
                                (user) => {
                                  if (user.id === e.target.value)
                                    return {
                                      ...user,
                                      checked: !user.checked,
                                    };
                                  return user;
                                }
                              );
                              setSearchResults(updatedSearchResults);
                            }}
                          />
                        </label>
                      )}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  } else {
    return null;
  }
}

interface SearchUsers extends SearchUsersResults {
  user: User | null;
}

export default function SearchUsers({
  currentMembers,
  searchResults,
  setSearchResults,
  user,
}: SearchUsers) {
  return (
    <div className="grid grid-flow-row gap-4">
      <SearchUsersBar setSearchResults={setSearchResults} user={user} />
      <SearchUsersResults
        currentMembers={currentMembers}
        searchResults={searchResults}
        setSearchResults={setSearchResults}
      />
    </div>
  );
}
