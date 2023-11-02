import axios from 'axios';
import { useState } from 'react';

import { User } from '../../../AuthContext';
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
      const response = await axios.get('/api/v1/users', { params: { q: searchValue } });
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
        className="w-full rounded-md border-gray-200 px-4 py-2.5 pe-10 shadow sm:text-sm"
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

function SearchUsersResults({ searchResults, setSearchResults }) {
  if (searchResults && searchResults.length > 0) {
    return (
      <div className="grid grid-flow-row gap-4">
        <span className="text-slate-600 font-bold">Search Results</span>
        <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
          <thead className="text-left">
            <tr>
              <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                Name
              </th>
              <th>
                <span
                  className="text-accent"
                  onClick={() => {
                    const updatedSearchResults = searchResults.map((user) => {
                      return { ...user, checked: true };
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
                  <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                    {user.first_name} {user.last_name}
                  </td>
                  <td className="text-center">
                    <label
                      htmlFor="AcceptConditions"
                      className="relative h-8 w-14 cursor-pointer"
                    >
                      <input
                        id={`${user.id}-search-checkbox`}
                        type="checkbox"
                        value={user.id}
                        checked={user.checked}
                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                        onChange={(e) => {
                          const updatedSearchResults = searchResults.map((user) => {
                            if (user.id === e.target.value)
                              return { ...user, checked: !user.checked };
                            return user;
                          });
                          setSearchResults(updatedSearchResults);
                        }}
                      />
                    </label>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    );
  } else {
    return null;
  }
}

export default function SearchUsers({ searchResults, setSearchResults, user }) {
  return (
    <div className="grid grid-flow-row gap-4">
      <SearchUsersBar setSearchResults={setSearchResults} user={user} />
      <SearchUsersResults
        searchResults={searchResults}
        setSearchResults={setSearchResults}
      />
    </div>
  );
}
