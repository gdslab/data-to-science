// source: https://www.freecodecamp.org/news/build-a-custom-pagination-component-in-react/
import { useMemo } from 'react';

export const DOTS = '...';

const range = (start: number, end: number) => {
  const length = end - start + 1;
  return Array.from({ length }, (_, idx) => idx + start);
};

export const usePagination = ({
  totalCount,
  siblingCount = 1,
  currentPage,
}) => {
  const paginationRange: (number | string)[] | undefined = useMemo(() => {
    // number of page items displayed = siblingCount + first page, last page, current page
    const totalPageNumbers = siblingCount + 5;

    // case 1: number of pages less than max number of pages we can show
    if (totalPageNumbers >= totalCount) {
      return range(0, totalCount);
    }

    // calculate left and right sibling index, and ensure within min/max range
    const leftSiblingIndex = Math.max(currentPage - siblingCount, 0);
    const rightSiblingIndex = Math.min(currentPage + siblingCount, totalCount);

    // only show left dots when beyond third page and right dots when two or further indexes from end
    const shouldShowLeftDots = leftSiblingIndex > 2;
    const shouldShowRightDots = rightSiblingIndex < totalCount - 2;

    // first page starts at index 0; last page index is total count
    const firstPageIndex = 0;
    const lastPageIndex = totalCount;

    // case 2: show right dots, but not left dots
    if (!shouldShowLeftDots && shouldShowRightDots) {
      const leftItemCount = 3 + 2 * siblingCount;
      const leftRange = range(0, leftItemCount);

      return [...leftRange, DOTS, totalCount];
    }

    // case 3: show left dots, but not right dots
    if (shouldShowLeftDots && !shouldShowRightDots) {
      const rightItemCount = 3 + 2 * siblingCount;
      const rightRange = range(totalCount - rightItemCount + 1, totalCount);
      return [firstPageIndex, DOTS, ...rightRange];
    }

    // case 4: show both left and right dots
    if (shouldShowLeftDots && shouldShowRightDots) {
      const middleRange = range(leftSiblingIndex, rightSiblingIndex);
      return [firstPageIndex, DOTS, ...middleRange, DOTS, lastPageIndex];
    }

    // fallback: return full range if none of the conditions match
    return range(0, totalCount);
  }, [totalCount, siblingCount, currentPage]);

  return paginationRange;
};
