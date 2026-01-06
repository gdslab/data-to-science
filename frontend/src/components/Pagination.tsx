import clsx from 'clsx';

import { DOTS, usePagination } from './hooks/usePagination';

/**
 * Displays total number of search results and range of results on current page.
 * @param {number} currentPageNum Current pagination page number.
 * @param {number} maxItemsPerPage Max number of items allowed on page.
 * @param {number} numOfItemsOnPage Number of items on current page.
 * @param {number} totalFilteredItems Overall total number of filtered items.
 * @returns Span element for summarizing search results.
 */
export function getPaginationResults(
  currentPageNum: number,
  maxItemsPerPage: number,
  numOfItemsOnPage: number,
  totalFilteredItems: number
) {
  if (numOfItemsOnPage <= 1 && currentPageNum === 0) {
    // either 0 of 0 or 1 of 1 being displayed
    return (
      <span className="text-sm text-gray-600">
        {numOfItemsOnPage} of {numOfItemsOnPage}
      </span>
    );
  } else {
    // if max items = 10; page 1 = 1 of ..., page 2 = 11 of ..., page 3 = 21 of ...
    const startItemOnPage = currentPageNum * maxItemsPerPage + 1;
    // if max items = 10; page 1 = ... of 10, page 2 = ... of 20, page 3 = ... of 30
    const endItemOnPage = currentPageNum * maxItemsPerPage + numOfItemsOnPage;

    return (
      <span className="text-sm text-gray-600">
        {startItemOnPage}-{endItemOnPage} of {totalFilteredItems}
      </span>
    );
  }
}

function PageNumberItems({
  paginationRange,
  currentPage,
  updateCurrentPage,
}: {
  paginationRange: ReturnType<typeof usePagination>;
  currentPage: number;
  updateCurrentPage: (page: number) => void;
}) {
  if (!paginationRange) return null;

  return (
    <>
      {paginationRange.map((pageNumber, idx) => {
        if (pageNumber === DOTS) {
          return (
            <li
              key={`dots-${idx}`}
              className="block size-8 rounded-sm text-center leading-8"
            >
              &#8230;
            </li>
          );
        }

        if (typeof pageNumber === 'number') {
          return (
            <li className="cursor-pointer" key={pageNumber}>
              <a
                onClick={() => updateCurrentPage(pageNumber)}
                className={clsx(
                  'block size-8 rounded-sm text-center leading-8',
                  {
                    'border border-gray-100 bg-white text-gray-900':
                      pageNumber !== currentPage,
                    'border-accent2 bg-accent2 text-white':
                      pageNumber === currentPage,
                  }
                )}
              >
                {pageNumber + 1}
              </a>
            </li>
          );
        }

        return null;
      })}
    </>
  );
}

export default function Pagination({
  currentPage,
  updateCurrentPage,
  totalPages,
}: {
  currentPage: number;
  updateCurrentPage: (page: number) => void;
  totalPages: number;
}) {
  const siblingCount = 2;
  const totalCount = totalPages - 1;

  const paginationRange = usePagination({
    currentPage,
    totalCount,
    siblingCount,
  });

  if (totalPages > 1) {
    return (
      <ol className="flex items-center justify-center gap-1 text-xs font-medium">
        <li>
          <a
            onClick={() => updateCurrentPage(currentPage - 1)}
            className={clsx(
              'inline-flex size-8 items-center justify-center rounded-sm border border-gray-100 bg-white text-gray-900',
              {
                'opacity-75 cursor-not-allowed': currentPage < 1,
                'cursor-pointer': currentPage > 0,
              }
            )}
          >
            <span className="sr-only">Prev Page</span>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-3 w-3"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </a>
        </li>

        <PageNumberItems
          paginationRange={paginationRange}
          currentPage={currentPage}
          updateCurrentPage={updateCurrentPage}
        />

        <li>
          <a
            onClick={() => updateCurrentPage(currentPage + 1)}
            className={clsx(
              'inline-flex size-8 items-center justify-center rounded-sm border border-gray-100 bg-white text-gray-900',
              {
                'opacity-75 cursor-not-allowed': currentPage + 1 >= totalPages,
                'cursor-pointer': currentPage + 1 < totalPages,
              }
            )}
          >
            <span className="sr-only">Next Page</span>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-3 w-3"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </a>
        </li>
      </ol>
    );
  } else {
    return null;
  }
}
