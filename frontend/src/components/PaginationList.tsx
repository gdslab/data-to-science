import { ReactNode, useEffect, useState } from 'react';

import Pagination from './Pagination';
import { IForester } from './pages/projects/Project';

export default function PaginationList({
  children,
  dataList,
  maxItems = 12,
  searchKeywords = [],
  searchText = '',
  updatePageData,
}: {
  children: ReactNode;
  dataList: any[];
  maxItems?: number;
  searchKeywords?: string[];
  searchText?: string;
  updatePageData: (pageData: IForester[]) => void;
}) {
  const [currentPage, setCurrentPage] = useState(0);

  const TOTAL_PAGES = Math.ceil(dataList.length / maxItems);

  /**
   * Updates the current selected pagination page.
   * @param newPage Index of new page.
   */
  function updateCurrentPage(newPage: number): void {
    const total_pages = Math.ceil(dataList.length / maxItems);

    if (newPage + 1 > total_pages) {
      setCurrentPage(total_pages - 1);
    } else if (newPage < 0) {
      setCurrentPage(0);
    } else {
      setCurrentPage(newPage);
    }
  }

  /**
   * Filters dataList by search text.
   * @param dataList Array of objects to filter.
   * @returns Filtered objects.
   */
  function filterSearch<T extends Record<string, any>>(dataList: T[]): T[] {
    if (!searchText) return dataList;

    return dataList.filter((data) => {
      searchKeywords.some(
        (keyword) =>
          typeof data?.[keyword] === 'string' &&
          data[keyword].toLowerCase().includes(searchText.toLowerCase())
      );
    });
  }

  /**
   * Filters dataList by search text and limits to current page.
   * @param dataList Array of objects
   * @returns Filtered objects.
   */
  function filterAndSlice<T extends Record<string, any>>(dataList: T[]): T[] {
    return filterSearch(dataList).slice(
      currentPage * maxItems,
      maxItems + currentPage * maxItems
    );
  }

  useEffect(() => {
    if (filterAndSlice(dataList).length < maxItems) {
      setCurrentPage(0);
    }
  }, [searchText]);

  useEffect(() => {
    updatePageData(filterAndSlice(dataList));
  }, [currentPage, dataList, TOTAL_PAGES]);

  return (
    <div className="h-full w-full flex flex-col gap-4">
      <div className="grow overflow-y-auto">{children}</div>
      {/* Pagination */}
      <div className="shrink-0 h-8 w-full bg-slate-200 px-6">
        <div className="flex justify-center">
          <Pagination
            currentPage={currentPage}
            totalPages={TOTAL_PAGES}
            updateCurrentPage={updateCurrentPage}
          />
        </div>
      </div>
    </div>
  );
}
