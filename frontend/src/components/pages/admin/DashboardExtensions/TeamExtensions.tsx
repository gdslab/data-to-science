import { useMemo, useState } from 'react';

import { Status } from '../../../Alert';
import { DataCard } from '../DataCards';
import ExtensionList, { Extension } from './ExtensionList';
import Pagination from '../../../Pagination';
import { Team } from '../../teams/Teams';
import SearchBar from '../SearchBar';

import { usePaginatedList } from '../../../hooks';
import { sorter } from '../../../utils';

const MAX_ITEMS = 10; // max number of teams per page

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
  const [searchTerm, setSearchTerm] = useState<string>('');

  const updateSearchTerm = (newSearchTerm: string): void =>
    setSearchTerm(newSearchTerm);

  const filteredTeams = useMemo(() => {
    // If searchTerm is empty, return all teams
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

  const { pageItems, totalPages, currentPage, updateCurrentPage } =
    usePaginatedList(filteredTeams, MAX_ITEMS);

  return (
    <div className="max-h-[60vh] flex flex-col gap-4">
      <h2>Teams</h2>
      <SearchBar
        searchTerm={searchTerm}
        updateSearchTerm={updateSearchTerm}
        placeholder="Search by team name or description"
      />

      {filteredTeams.length === 0 ? (
        <p className="text-gray-500">No teams match your search.</p>
      ) : (
        <>
          {/* Header and body live in one table so the columns stay aligned; the
              sticky header pins to the top of the shared scroll container. */}
          <div className="hidden max-h-96 overflow-y-auto md:block">
            <table className="relative w-full border-separate border-spacing-y-1 border-spacing-x-1">
              <thead>
                <tr className="h-12 text-slate-700">
                  <th className="sticky top-0 z-10 w-1/2 bg-slate-300">Name</th>
                  <th className="sticky top-0 z-10 w-1/2 bg-slate-300">
                    Extensions
                  </th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((team) => (
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

          {/* The name column plus a checkbox row cannot fit a phone, so the same
              rows render as cards below `md`. */}
          <div className="flex flex-col gap-3 md:hidden">
            {pageItems.map((team) => (
              <DataCard
                key={team.id}
                title={team.title}
                subtitle={team.description}
              >
                <div className="mt-3">
                  <ExtensionList
                    extensions={extensions}
                    selectedExtensions={team.exts}
                    setStatus={setStatus}
                    teamId={team.id}
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
