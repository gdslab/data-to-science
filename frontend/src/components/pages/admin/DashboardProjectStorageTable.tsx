import { useMemo, useState } from 'react';

import { ProjectStatistics } from './DashboardTypes';
import Pagination from '../../Pagination';

export default function DashboardProjectStorageTable({
  userProjectStats,
}: {
  userProjectStats: ProjectStatistics[];
}) {
  const [currentPage, setCurrentPage] = useState(0);

  const MAX_ITEMS = 5; // max number of users per page
  const TOTAL_PAGES = Math.ceil(userProjectStats.length / MAX_ITEMS);

  /**
   * Updates the current selected pagination page.
   * @param newPage Index of new page.
   */
  function updateCurrentPage(newPage: number): void {
    const total_pages = Math.ceil(
      userProjectStats ? userProjectStats.length : 0 / MAX_ITEMS
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
   * Filters users by search text and limits to current page.
   * @param users Users to filter.
   * @returns
   */
  function filterAndSlice(stats: ProjectStatistics[]) {
    return stats.slice(
      currentPage * MAX_ITEMS,
      MAX_ITEMS + currentPage * MAX_ITEMS
    );
  }

  /**
   * Returns available users on page limitations.
   * @param users Users to filter, limit, and sort.
   * @returns Array of filtered users.
   */
  function getAvailableUsers(stats): ProjectStatistics[] {
    return filterAndSlice(stats);
  }

  const userProjectStatsSorted = useMemo(() => {
    return [...userProjectStats].sort(
      (a, b) => b.total_storage - a.total_storage
    );
  }, [userProjectStats]);

  if (userProjectStats.length === 0) {
    return <section className="w-full bg-white">No data</section>;
  }

  return (
    <div className="relative mt-12">
      <table className="relative w-full border-separate border-spacing-y-1 border-spacing-x-1">
        <thead>
          <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
            <th className="p-2">Name</th>
            <th className="p-2">Projects*</th>
            <th className="p-2">Total storage GB**</th>
          </tr>
        </thead>
        <tbody className="max-h-96 overflow-y-auto">
          {getAvailableUsers(userProjectStatsSorted).map((stats) => (
            <tr key={stats.id} className="text-center">
              <td className="p-2 bg-slate-100 w-96 max-w-96 truncate">
                {stats.user}
              </td>
              <td className="p-2 bg-slate-50 w-44">
                {stats.total_projects} ({stats.total_active_projects})
              </td>
              <td className="p-2 bg-slate-50 w-48">
                {(stats.total_storage / 1024 ** 3).toFixed(3)} (
                {(stats.total_active_storage / 1024 ** 3).toFixed(3)})
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <Pagination
        currentPage={currentPage}
        updateCurrentPage={updateCurrentPage}
        totalPages={TOTAL_PAGES}
      />
      <div className="mt-4 text-left">
        <div className="relative">* Total projects (total active projects)</div>
        <div className="relative">
          ** Total storage (total storage from active projects)
        </div>
      </div>
    </div>
  );
}
