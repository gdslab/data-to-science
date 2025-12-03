import { useEffect, useRef } from 'react';

export default function Filter({
  categories,
  selectedCategory,
  setSelectedCategory,
  isOpen,
  onOpen,
  onClose,
  sublistParentValue,
  sublistCategories,
  sublistSelected,
  setSublistSelected,
}: {
  categories: { label: string; value: string }[];
  selectedCategory: string[];
  setSelectedCategory: (selectedCategories: string[]) => void;
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  sublistParentValue?: string;
  sublistCategories?: { label: string; value: string }[];
  sublistSelected?: string[];
  setSublistSelected?: (selected: string[]) => void;
}) {
  const detailsRef = useRef<HTMLDetailsElement>(null);

  /**
   * Closes the Filter by ... details element on click outside element
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (detailsRef.current?.open && event.target) {
        if (!detailsRef.current.contains(event.target as HTMLElement)) {
          detailsRef.current.removeAttribute('open');
          onClose();
        }
      }
    };

    window.addEventListener('click', handleClickOutside);
    return () => {
      window.removeEventListener('click', handleClickOutside);
    };
  }, [onClose]);

  function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.checked) {
      setSelectedCategory([...selectedCategory, e.target.value]);
    } else {
      const next = selectedCategory.filter(
        (category) => category !== e.target.value
      );
      setSelectedCategory(next);
      if (
        sublistParentValue &&
        setSublistSelected &&
        sublistSelected &&
        e.target.value === sublistParentValue
      ) {
        setSublistSelected([]);
      }
    }
  }

  function onSubChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (!setSublistSelected || !sublistSelected) return;
    if (e.target.checked) {
      setSublistSelected([...sublistSelected, e.target.value]);
    } else {
      setSublistSelected(
        sublistSelected.filter((value) => value !== e.target.value)
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
            <span className="text-sm font-medium"> Filter by </span>

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
            <div className="min-w-[200px] max-w-[300px] rounded-sm border border-gray-200 bg-white">
              <header className="flex items-center justify-between p-4">
                <span className="text-sm text-gray-700">
                  {' '}
                  {selectedCategory.length} Selected{' '}
                </span>

                <button
                  type="button"
                  className="text-sm text-gray-900 underline underline-offset-4"
                  onClick={() => {
                    setSelectedCategory([]);
                    if (setSublistSelected) setSublistSelected([]);
                  }}
                >
                  Reset
                </button>
              </header>

              <ul className="space-y-1 border-t border-gray-200 p-4">
                {categories.map((category) => {
                  const isParent =
                    sublistParentValue && category.value === sublistParentValue;
                  const parentChecked =
                    selectedCategory.indexOf(category.value) > -1;
                  return (
                    <li key={category.value}>
                      <label
                        htmlFor={category.value}
                        className="inline-flex items-center gap-2"
                      >
                        <input
                          type="checkbox"
                          id={category.value}
                          className="size-5 rounded-sm text-accent2 border-gray-300"
                          value={category.value}
                          checked={parentChecked}
                          onChange={onChange}
                        />
                        <span className="text-sm font-medium text-gray-700">
                          {' '}
                          {category.label}{' '}
                        </span>
                      </label>
                      {isParent && parentChecked && sublistCategories && (
                        <ul className="mt-2 ml-6 pl-1 space-y-1 h-60 overflow-y-auto">
                          {sublistCategories.map((sub) => (
                            <li key={sub.value}>
                              <label
                                htmlFor={`${category.value}-${sub.value}`}
                                className="inline-flex items-center gap-2"
                              >
                                <input
                                  type="checkbox"
                                  id={`${category.value}-${sub.value}`}
                                  className="size-4 rounded-sm text-accent2 border-gray-300"
                                  value={sub.value}
                                  checked={
                                    !!sublistSelected &&
                                    sublistSelected.indexOf(sub.value) > -1
                                  }
                                  onChange={onSubChange}
                                />
                                <span
                                  className="text-sm text-gray-700 inline-block w-[120px] truncate"
                                  title={sub.label}
                                >
                                  {sub.label}
                                </span>
                              </label>
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
        </details>
      </div>
    </div>
  );
}
