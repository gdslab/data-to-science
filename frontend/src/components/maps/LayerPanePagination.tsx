import clsx from 'clsx';

export default function LayerPanePagination({
  currentPage,
  updateCurrentPage,
  totalPages,
}: {
  currentPage: number;
  updateCurrentPage: (page: number) => void;
  totalPages: number;
}) {
  function PageNumberItems() {
    let pageNumberItems: JSX.Element[] = [];
    for (let i = 0; i < totalPages; i++) {
      pageNumberItems.push(
        <li className="cursor-pointer" key={`page-${i}`}>
          <a
            onClick={() => updateCurrentPage(i)}
            className={clsx('block size-8 rounded text-center leading-8', {
              'border border-gray-100 bg-white text-gray-900': currentPage !== i,
              'border-blue-600 bg-blue-600 text-white': currentPage === i,
            })}
          >
            {(i + 1).toString()}
          </a>
        </li>
      );
    }
    return pageNumberItems;
  }

  if (totalPages > 1) {
    return (
      <ol className="flex justify-center gap-1 text-xs font-medium">
        <li>
          <a
            onClick={() => updateCurrentPage(currentPage - 1)}
            className={clsx(
              'inline-flex size-8 items-center justify-center rounded border border-gray-100 bg-white text-gray-900',
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

        <PageNumberItems />

        <li>
          <a
            onClick={() => updateCurrentPage(currentPage + 1)}
            className={clsx(
              'inline-flex size-8 items-center justify-center rounded border border-gray-100 bg-white text-gray-900',
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
