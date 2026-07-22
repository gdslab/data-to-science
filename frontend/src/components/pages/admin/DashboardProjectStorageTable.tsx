import { useMemo, useState } from 'react';

import { DataCard, MetricTile, MetricTileGrid } from './DataCards';
import { ProjectStatistics } from './DashboardTypes';
import Pagination from '../../Pagination';
import SearchBar from './SearchBar';

import { usePaginatedList } from '../../hooks';
import { bytesToGB } from '../../utils';

const MAX_ITEMS = 10; // max number of users per page

export default function DashboardProjectStorageTable({
  userProjectStats,
}: {
  userProjectStats: ProjectStatistics[];
}) {
  const [searchTerm, setSearchTerm] = useState<string>('');

  const updateSearchTerm = (newSearchTerm: string): void =>
    setSearchTerm(newSearchTerm);

  // Rank against every user before filtering so a searched user keeps the
  // position they hold overall rather than being renumbered within the results.
  const rankedStats = useMemo(
    () =>
      [...userProjectStats]
        .sort((a, b) => b.total_active_storage - a.total_active_storage)
        .map((stats, idx) => ({ ...stats, rank: idx + 1 })),
    [userProjectStats]
  );

  const visibleStats = useMemo(() => {
    const lowerSearchTerm = searchTerm.trim().toLowerCase();
    if (!lowerSearchTerm) return rankedStats;

    return rankedStats.filter((stats) =>
      stats.user.toLowerCase().includes(lowerSearchTerm)
    );
  }, [searchTerm, rankedStats]);

  const { pageItems, currentPage, totalPages, updateCurrentPage } =
    usePaginatedList(visibleStats, MAX_ITEMS);

  if (userProjectStats.length === 0) {
    return <section className="w-full bg-white">No data</section>;
  }

  return (
    <div className="relative mt-12 flex flex-col gap-4">
      <SearchBar
        searchTerm={searchTerm}
        updateSearchTerm={updateSearchTerm}
        placeholder="Search by user name"
      />

      {visibleStats.length === 0 ? (
        <p className="text-gray-500">No users match your search.</p>
      ) : (
        <>
          <table className="relative hidden w-full border-separate border-spacing-y-1 border-spacing-x-1 md:table">
            <thead>
              <tr className="h-12 text-slate-700 bg-slate-300">
                <th className="p-2 w-16">#</th>
                <th className="p-2">Name</th>
                <th className="p-2">Projects</th>
                <th className="p-2">Storage (GB)</th>
              </tr>
            </thead>
            <tbody>
              {pageItems.map((stats) => (
                <tr key={stats.id} className="text-center">
                  <td className="p-2 bg-slate-100 w-16 font-semibold text-gray-500">
                    {stats.rank}
                  </td>
                  <td className="p-2 bg-slate-100 w-96 max-w-96 truncate">
                    {stats.user}
                  </td>
                  <td className="p-2 bg-slate-50 w-44">
                    {stats.total_active_projects}
                  </td>
                  <td className="p-2 bg-slate-50 w-48">
                    {bytesToGB(stats.total_active_storage)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* The table's fixed column widths cannot fit a phone without
              horizontal scrolling, so the same rows render as cards below `md`. */}
          <div className="flex flex-col gap-3 md:hidden">
            {pageItems.map((stats) => (
              <DataCard
                key={stats.id}
                leading={
                  <span className="shrink-0 text-sm font-semibold text-gray-500">
                    #{stats.rank}
                  </span>
                }
                title={stats.user}
              >
                <MetricTileGrid>
                  <MetricTile
                    label="Projects"
                    value={stats.total_active_projects}
                  />
                  <MetricTile
                    label="Storage (GB)"
                    value={bytesToGB(stats.total_active_storage)}
                    highlight
                  />
                </MetricTileGrid>
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
