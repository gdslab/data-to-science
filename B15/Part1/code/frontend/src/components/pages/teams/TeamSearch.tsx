import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

export default function TeamSearch({
  value,
  onChange,
}: {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <div className="relative flex items-center w-full">
      <MagnifyingGlassIcon className="absolute left-3 h-4 w-4 text-gray-400" />
      <input
        type="text"
        placeholder="Search teams"
        className="w-full rounded-md border-gray-200 pl-10 pr-4 py-2.5 text-black sm:text-sm shadow-sm bg-white placeholder:text-gray-400"
        value={value}
        onChange={onChange}
      />
    </div>
  );
}
