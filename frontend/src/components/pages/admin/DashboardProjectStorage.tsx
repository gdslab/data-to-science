import axios, { AxiosResponse } from 'axios';
import { useMemo, useState } from 'react';
import { useLoaderData } from 'react-router-dom';

import { ProjectStatistics } from './DashboardTypes';
import Pagination from '../../Pagination';

export async function loader() {
  try {
    const response: AxiosResponse<ProjectStatistics[]> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/admin/project_statistics`
    );
    if (response.status === 200) {
      return response.data;
    } else {
      return [];
    }
  } catch (_err) {
    return [];
  }
}

export default function DashboardProjectStorage() {
  const userProjectStats = useLoaderData() as ProjectStatistics[];

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
    return stats.slice(currentPage * MAX_ITEMS, MAX_ITEMS + currentPage * MAX_ITEMS);
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
    return [...getAvailableUsers(userProjectStats)].sort(
      (a, b) => b.total_storage - a.total_storage
    );
  }, [userProjectStats]);

  if (userProjectStats.length === 0) {
    return <section className="w-full bg-white">No data</section>;
  }

  return (
    <section className="w-full bg-white">
      <div className="h-full mx-auto max-w-screen-xl px-4 py-12 sm:px-6 md:py-16 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            User Project Storage
          </h2>

          <p className="mt-4 text-gray-500 sm:text-xl">
            Summary of total disk usage by user based on project ownership.
          </p>
        </div>
        <table className="relative w-full border-separate border-spacing-y-1 border-spacing-x-1">
          <thead>
            <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
              <th className="p-4">Name</th>
              <th className="p-4">Total projects</th>
              <th className="p-4">Total storage (GB)</th>
            </tr>
          </thead>
          <tbody className="max-h-96 overflow-y-auto">
            {userProjectStatsSorted.map((stats) => (
              <tr key={stats.id} className="text-center">
                <td className="p-4 bg-slate-100">{stats.user}</td>
                <td className="p-4 bg-white">{stats.total_projects}</td>
                <td>{(stats.total_storage / 1024 ** 3).toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <Pagination
          currentPage={currentPage}
          updateCurrentPage={updateCurrentPage}
          totalPages={TOTAL_PAGES}
        />
      </div>
    </section>
  );
}
