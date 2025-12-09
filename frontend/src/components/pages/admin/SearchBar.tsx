type SearchTermProps = {
  searchTerm: string;
  updateSearchTerm: (newSearchTerm: string) => void;
};

export default function SearchBar({
  searchTerm,
  updateSearchTerm,
}: SearchTermProps) {
  return (
    <div className="relative">
      <label htmlFor="Search" className="sr-only">
        {' '}
        Search{' '}
      </label>

      <input
        type="text"
        id="Search"
        placeholder="Search by table by keyword"
        className="w-full rounded-md border-gray-200 px-4 py-2.5 pe-10 shadow-sm sm:text-sm"
        value={searchTerm}
        onChange={(e) => updateSearchTerm(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            // searchUsers();
            // updateSearchTerm('');
          }
        }}
      />

      <span className="absolute inset-y-0 end-0 grid w-10 place-content-center">
        <button
          type="button"
          className="text-gray-600 hover:text-gray-700 cursor-pointer"
          onClick={() => {
            // searchUsers();
            // updateSearchTerm('');
          }}
        >
          <span className="sr-only">Search</span>

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
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
            />
          </svg>
        </button>
      </span>
    </div>
  );
}
