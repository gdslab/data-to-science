import { useEffect, useMemo, useState } from 'react';

type PaginatedList<T> = {
  pageItems: T[];
  currentPage: number;
  totalPages: number;
  updateCurrentPage: (newPage: number) => void;
};

/**
 * Slices a list into pages and tracks the active page.
 * @param items Full list to paginate.
 * @param maxItems Maximum number of items per page.
 * @returns Items on the current page plus the state needed by Pagination.
 */
export function usePaginatedList<T>(
  items: T[],
  maxItems: number
): PaginatedList<T> {
  const [currentPage, setCurrentPage] = useState(0);

  const totalPages = Math.ceil(items.length / maxItems);

  // Pull the page back in bounds when the list shrinks beneath it, e.g. after a
  // search term filters out everything on the current page.
  useEffect(() => {
    if (currentPage > 0 && currentPage >= totalPages) {
      setCurrentPage(Math.max(0, totalPages - 1));
    }
  }, [currentPage, totalPages]);

  function updateCurrentPage(newPage: number): void {
    setCurrentPage(Math.max(0, Math.min(newPage, totalPages - 1)));
  }

  const pageItems = useMemo(
    () => items.slice(currentPage * maxItems, maxItems + currentPage * maxItems),
    [items, currentPage, maxItems]
  );

  return { pageItems, currentPage, totalPages, updateCurrentPage };
}
