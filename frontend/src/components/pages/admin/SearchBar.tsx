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
          }
        }}
      />
    </div>
  );
}
