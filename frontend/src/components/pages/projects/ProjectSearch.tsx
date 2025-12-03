type ProjectSearch = {
  searchText: string;
  updateSearchText: (e: any) => void;
};

export default function ProjectSearch({ searchText, updateSearchText }: ProjectSearch) {
  return (
    <div className="relative w-full">
      <label htmlFor="Search" className="sr-only">
        {' '}
        Search{' '}
      </label>
      <label htmlFor="Search" className="sr-only">
        {' '}
        Search{' '}
      </label>
      <input
        type="text"
        id="Search"
        placeholder="Search for project by title or description"
        className="w-full rounded-md border-gray-200 px-4 py-2.5 pe-10 shadow-sm sm:text-sm"
        value={searchText}
        onChange={(e) => updateSearchText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            updateSearchText('');
          }
        }}
      />
      <span className="absolute inset-y-0 end-0 grid w-10 place-content-center">
        <span className="sr-only">Search</span>

        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth="1.5"
          stroke="currentColor"
          className="h-4 w-4 text-slate-400"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
          />
        </svg>
      </span>
    </div>
  );
}
