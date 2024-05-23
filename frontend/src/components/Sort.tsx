import { useEffect, useRef } from 'react';

export type SortSelection = 'atoz' | 'ztoa';
type SetSortSelection = React.Dispatch<React.SetStateAction<'atoz' | 'ztoa'>>;

export default function Sort({
  sortSelection,
  setSortSelection,
}: {
  sortSelection: SortSelection;
  setSortSelection: SetSortSelection;
}) {
  const categories = [
    { key: 'atoz', label: 'Title A-Z' },
    { key: 'ztoa', label: 'Title Z-A' },
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
        }
      }
    });
  }, []);

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
      if (event.target.value === 'atoz' || event.target.value === 'ztoa')
        setSortSelection(event.target.value);
    }
  }

  return (
    <div className="flex gap-8">
      <div className="relative">
        <details
          ref={detailsRef}
          className="group [&_summary::-webkit-details-marker]:hidden"
        >
          <summary className="flex cursor-pointer items-center gap-2 border-b border-gray-400 pb-1 text-gray-900 transition hover:border-gray-600">
            <span className="text-sm font-medium">
              {' '}
              Sort by: {getSortOptionLabel(sortSelection)}{' '}
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
            <div className="w-96 rounded border border-gray-200 bg-white">
              <ul className="space-y-1 border-t border-gray-200 p-4">
                {categories.map(({ key, label }) => (
                  <li key={key}>
                    <label htmlFor={key} className="inline-flex items-center gap-2">
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
                        {' '}
                        {label}{' '}
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
