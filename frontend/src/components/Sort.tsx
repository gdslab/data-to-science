import { useEffect, useRef } from 'react';
import { Project } from './pages/projects/ProjectList';

import { sorter } from './utils';

export type SortSelection =
  | 'atoz'
  | 'ztoa'
  | 'recent'
  | 'mostflights'
  | 'leastflights'
  | 'mostdata'
  | 'leastdata';
type SetSortSelection = React.Dispatch<React.SetStateAction<SortSelection>>;

/**
 * Return true if sort option matches one of the accepted sort option values.
 * @param sortOption Sort option.
 * @returns True if sort option is valid.
 */
function isValidSortOption(sortOption: string): boolean {
  return (
    typeof sortOption === 'string' &&
    (sortOption === 'atoz' || sortOption === 'ztoa' || sortOption === 'recent')
  );
}

/**
 * Get sort preference from local storage (if available).
 * @param key Local storage key for sort preference.
 * @returns Sort preference stored in local storage or default value.
 */
export function getSortPreferenceFromLocalStorage(key: string): SortSelection {
  const sortOption = localStorage.getItem(key);
  if (sortOption && isValidSortOption(sortOption)) {
    // @ts-ignore isValidSortOption checks type
    return sortOption;
  } else {
    return 'atoz'; // default sort option
  }
}

/**
 * Set sort preference in local storage using provided key.
 * @param key Local storage key for sort preference.
 * @param sortOption Sort option.
 */
function setSortPreferenceInLocalStorage(
  key: string,
  sortOption: SortSelection
) {
  localStorage.setItem(key, sortOption);
}

/**
 * Sort array of projects by sort selection option.
 * @param projects Array of projects.
 * @param sortSelection Sort selection option.
 * @returns Array of sorted projects.
 */
export function sortProjects(
  projects: Project[],
  sortSelection: SortSelection
): Project[] {
  return projects.sort((a, b) => {
    // First sort by liked status (liked projects come first)
    if (a.liked !== b.liked) {
      return a.liked ? -1 : 1;
    }

    // Then apply the selected sort
    if (sortSelection === 'atoz') {
      return sorter(a.title.toLowerCase(), b.title.toLowerCase());
    } else if (sortSelection === 'ztoa') {
      return sorter(a.title.toLowerCase(), b.title.toLowerCase(), 'desc');
    } else if (sortSelection === 'recent') {
      return sorter(
        new Date(a.most_recent_flight),
        new Date(b.most_recent_flight),
        'desc'
      );
    } else if (sortSelection === 'mostflights') {
      return b.flight_count - a.flight_count;
    } else if (sortSelection === 'leastflights') {
      return a.flight_count - b.flight_count;
    } else if (sortSelection === 'mostdata') {
      return b.data_product_count - a.data_product_count;
    } else if (sortSelection === 'leastdata') {
      return a.data_product_count - b.data_product_count;
    } else {
      return sorter(a.title.toLowerCase(), b.title.toLowerCase());
    }
  });
}

export default function Sort({
  sortSelection,
  setSortSelection,
  isOpen,
  onOpen,
  onClose,
}: {
  sortSelection: SortSelection;
  setSortSelection: SetSortSelection;
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
}) {
  const categories = [
    {
      key: 'atoz',
      label: 'Title A-Z',
      title: 'Sort by title in ascending order',
    },
    {
      key: 'ztoa',
      label: 'Title Z-A',
      title: 'Sort by title in descending order',
    },
    {
      key: 'recent',
      label: 'Recent Flights',
      title: 'Sort by projects with most recent flights',
    },
    {
      key: 'mostflights',
      label: 'Most Flights',
      title: 'Sort by projects with most flights',
    },
    {
      key: 'leastflights',
      label: 'Least Flights',
      title: 'Sort by projects with least flights',
    },
    {
      key: 'mostdata',
      label: 'Most Data',
      title: 'Sort by projects with most data products',
    },
    {
      key: 'leastdata',
      label: 'Least Data',
      title: 'Sort by projects with least data products',
    },
  ];

  const detailsRef = useRef<HTMLDetailsElement>(null);

  /**
   * Closes the Sort by ... details element on click outside element
   */
  useEffect(() => {
    document.body.addEventListener('click', (event: MouseEvent) => {
      if (detailsRef.current && event.target) {
        if (!detailsRef.current.contains(event.target as HTMLElement)) {
          detailsRef.current.removeAttribute('open');
          onClose();
        }
      }
    });
  }, [onClose]);

  /**
   * Returns label for the currently selected sort option.
   * @param sortOption Currently selected sort option.
   * @returns Sort option label.
   */
  function getSortOptionLabel(sortOption: SortSelection) {
    const filteredOptions = categories.filter(({ key }) => key === sortOption);
    if (filteredOptions.length > 0) {
      return filteredOptions[0].label;
    } else {
      return 'Unknown';
    }
  }

  /**
   * Updates sort option selection when radio input changes.
   * @param event Change event fired when radio button selected.
   */
  function onChange(event: React.ChangeEvent<HTMLInputElement>) {
    if (event.target.checked) {
      if (
        event.target.value === 'atoz' ||
        event.target.value === 'ztoa' ||
        event.target.value === 'recent' ||
        event.target.value === 'mostflights' ||
        event.target.value === 'leastflights' ||
        event.target.value === 'mostdata' ||
        event.target.value === 'leastdata'
      )
        setSortSelection(event.target.value);
      // update sort option in local storage
      setSortPreferenceInLocalStorage(
        'sortPreference',
        event.target.value as SortSelection
      );
    }
  }

  return (
    <div className="flex gap-8">
      <div className="relative">
        <details
          ref={detailsRef}
          className="group [&_summary::-webkit-details-marker]:hidden"
          open={isOpen}
          onToggle={(e) => {
            if (e.currentTarget.open) {
              onOpen();
            } else {
              onClose();
            }
          }}
        >
          <summary className="flex cursor-pointer items-center gap-2 border-b border-gray-400 pb-1 text-gray-900 transition hover:border-gray-600">
            <span className="w-36 text-sm font-medium">
              Sort by: {getSortOptionLabel(sortSelection)}
            </span>

            <span className="transition group-open:-rotate-180">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                className="h-4 w-4"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19.5 8.25l-7.5 7.5-7.5-7.5"
                />
              </svg>
            </span>
          </summary>

          <div className="z-50 group-open:absolute group-open:start-0 group-open:top-auto group-open:mt-2">
            <div className="rounded border border-gray-200 bg-white">
              <ul className="space-y-1 border-t border-gray-200 p-4">
                {categories.map(({ key, label, title }) => (
                  <li key={key}>
                    <label
                      htmlFor={key}
                      className="inline-flex items-center gap-2"
                      title={title}
                    >
                      <input
                        type="radio"
                        name="sortOption"
                        id={key}
                        className="size-5 text-accent2 border-gray-300"
                        value={key}
                        checked={sortSelection === key}
                        onChange={onChange}
                      />
                      <span className="text-sm font-medium text-gray-700">
                        {label}
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </details>
      </div>
    </div>
  );
}
