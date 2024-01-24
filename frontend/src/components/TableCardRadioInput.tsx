export default function TableCardRadioInput({
  tableView,
  toggleTableView,
}: {
  tableView: 'table' | 'carousel';
  toggleTableView: React.Dispatch<React.SetStateAction<'table' | 'carousel'>>;
}) {
  function onChange(e) {
    toggleTableView(e.target.value);
  }

  return (
    <fieldset className="mb-4 flex flex-wrap justify-end">
      <legend className="sr-only">Toggle Table View</legend>

      <div>
        <input
          type="radio"
          name="toggleTableView"
          value="table"
          id="tableInput"
          className="peer hidden"
          checked={tableView === 'table'}
          onChange={onChange}
        />

        <label
          htmlFor="tableInput"
          className="flex cursor-pointer items-center justify-center rounded-l-md border border-gray-100 bg-white px-6 py-1.5 text-gray-900 hover:border-gray-200 peer-checked:border-accent3 peer-checked:bg-accent3 peer-checked:text-white"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="w-5 h-5"
          >
            <path
              fillRule="evenodd"
              d="M.99 5.24A2.25 2.25 0 0 1 3.25 3h13.5A2.25 2.25 0 0 1 19 5.25l.01 9.5A2.25 2.25 0 0 1 16.76 17H3.26A2.267 2.267 0 0 1 1 14.74l-.01-9.5Zm8.26 9.52v-.625a.75.75 0 0 0-.75-.75H3.25a.75.75 0 0 0-.75.75v.615c0 .414.336.75.75.75h5.373a.75.75 0 0 0 .627-.74Zm1.5 0a.75.75 0 0 0 .627.74h5.373a.75.75 0 0 0 .75-.75v-.615a.75.75 0 0 0-.75-.75H11.5a.75.75 0 0 0-.75.75v.625Zm6.75-3.63v-.625a.75.75 0 0 0-.75-.75H11.5a.75.75 0 0 0-.75.75v.625c0 .414.336.75.75.75h5.25a.75.75 0 0 0 .75-.75Zm-8.25 0v-.625a.75.75 0 0 0-.75-.75H3.25a.75.75 0 0 0-.75.75v.625c0 .414.336.75.75.75H8.5a.75.75 0 0 0 .75-.75ZM17.5 7.5v-.625a.75.75 0 0 0-.75-.75H11.5a.75.75 0 0 0-.75.75V7.5c0 .414.336.75.75.75h5.25a.75.75 0 0 0 .75-.75Zm-8.25 0v-.625a.75.75 0 0 0-.75-.75H3.25a.75.75 0 0 0-.75.75V7.5c0 .414.336.75.75.75H8.5a.75.75 0 0 0 .75-.75Z"
              clipRule="evenodd"
            />
          </svg>
          <span className="sr-only text-sm font-medium">Table</span>
        </label>
      </div>

      <div>
        <input
          type="radio"
          name="toggleTableView"
          value="carousel"
          id="carouselInput"
          className="peer hidden"
          checked={tableView === 'carousel'}
          onChange={onChange}
        />

        <label
          htmlFor="carouselInput"
          className="flex cursor-pointer items-center justify-center rounded-r-md border border-gray-100 bg-white px-6 py-1.5 text-gray-900 hover:border-gray-200 peer-checked:border-accent3 peer-checked:bg-accent3 peer-checked:text-white"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="w-5 h-5"
          >
            <path d="M14 17h2.75A2.25 2.25 0 0 0 19 14.75v-9.5A2.25 2.25 0 0 0 16.75 3H14v14ZM12.5 3h-5v14h5V3ZM3.25 3H6v14H3.25A2.25 2.25 0 0 1 1 14.75v-9.5A2.25 2.25 0 0 1 3.25 3Z" />
          </svg>

          <span className="sr-only text-sm font-medium">Carousel</span>
        </label>
      </div>
    </fieldset>
  );
}
