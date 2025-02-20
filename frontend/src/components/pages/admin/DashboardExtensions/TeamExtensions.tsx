import { useMemo, useState } from 'react';

import { Status } from '../../../Alert';
import ExtensionList, { Extension } from './ExtensionList';
import Pagination from '../../../Pagination';
import { Team } from '../../teams/Teams';
import SearchBar from '../SearchBar';

import { sorter } from '../../../utils';

type TeamExtensionsProps = {
  extensions: Extension[];
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
  teams: Team[];
};

export default function TeamExtensions({
  extensions,
  setStatus,
  teams,
}: TeamExtensionsProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [searchTerm, setSearchTerm] = useState<string>('');

  const updateSearchTerm = (newSearchTerm: string): void =>
    setSearchTerm(newSearchTerm);

  const filteredTeams = useMemo(() => {
    // If searchTerm is empty, return all users
    if (searchTerm === '') {
      return teams
        .slice()
        .sort((a, b) => sorter(a.title.toLowerCase(), b.title.toLowerCase()));
    }

    const lowerSearchTerm = searchTerm.toLowerCase();

    return teams
      .filter(
        (team) =>
          team.title.toLowerCase().includes(lowerSearchTerm) ||
          team.description.toLowerCase().includes(lowerSearchTerm)
      )
      .sort((a, b) => sorter(a.title.toLowerCase(), b.title.toLowerCase()));
  }, [searchTerm, teams]);

  const MAX_ITEMS = 10; // max number of users per page
  const TOTAL_PAGES = Math.ceil(filteredTeams.length / MAX_ITEMS);

  /**
   * Updates the current selected pagination page.
   * @param newPage Index of new page.
   */
  function updateCurrentPage(newPage: number): void {
    const total_pages = Math.ceil(
      filteredTeams ? filteredTeams.length : 0 / MAX_ITEMS
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
  function filterAndSlice(items: Team[]) {
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
  function getAvailableUsers(items: Team[]): Team[] {
    return filterAndSlice(items);
  }

  return (
    <div className="max-h-[60vh] flex flex-col gap-4">
      <h2>Teams</h2>
      <SearchBar searchTerm={searchTerm} updateSearchTerm={updateSearchTerm} />
      <table className="relative border-separate border-spacing-y-1 border-spacing-x-1">
        <thead>
          <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
            <th className="w-1/2">Name</th>
            <th className="w-1/2">Extensions</th>
          </tr>
        </thead>
      </table>
      <div className="max-h-96 overflow-y-auto">
        <table className="relative border-separate border-spacing-y-1 border-spacing-x-1">
          <tbody>
            {getAvailableUsers(filteredTeams).map((team) => (
              <tr key={team.id} className="text-center">
                <td className="w-1/2 p-1.5 bg-slate-100">{team.title}</td>
                <td className="w-1/2 p-1.5 bg-white">
                  <ExtensionList
                    extensions={extensions}
                    selectedExtensions={team.exts}
                    setStatus={setStatus}
                    teamId={team.id}
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
