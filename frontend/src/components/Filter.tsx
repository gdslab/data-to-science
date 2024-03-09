export default function Filter({
  categories,
  selectedCategory,
  setSelectedCategory,
}: {
  categories: string[];
  selectedCategory: string[];
  setSelectedCategory: (selectedCategories: string[]) => void;
}) {
  function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.checked) {
      setSelectedCategory([...selectedCategory, e.target.value]);
    } else {
      setSelectedCategory([
        ...selectedCategory.filter((category) => category !== e.target.value),
      ]);
    }
  }

  return (
    <div className="flex gap-8">
      <div className="relative">
        <details className="group [&_summary::-webkit-details-marker]:hidden">
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
            <div className="w-96 rounded border border-gray-200 bg-white">
              <header className="flex items-center justify-between p-4">
                <span className="text-sm text-gray-700">
                  {' '}
                  {selectedCategory.length} Selected{' '}
                </span>

                <button
                  type="button"
                  className="text-sm text-gray-900 underline underline-offset-4"
                  onClick={() => setSelectedCategory([])}
                >
                  Reset
                </button>
              </header>

              <ul className="space-y-1 border-t border-gray-200 p-4">
                {categories.map((category) => (
                  <li key={category}>
                    <label
                      htmlFor={category}
                      className="inline-flex items-center gap-2"
                    >
                      <input
                        type="checkbox"
                        id={category}
                        className="size-5 rounded text-accent2 border-gray-300"
                        value={category}
                        checked={selectedCategory.indexOf(category) > -1}
                        onChange={onChange}
                      />
                      <span className="text-sm font-medium text-gray-700">
                        {' '}
                        {category}{' '}
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
