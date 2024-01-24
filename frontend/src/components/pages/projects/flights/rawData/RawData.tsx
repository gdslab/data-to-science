import { TrashIcon } from '@heroicons/react/24/outline';
import { RawData as RawDataInterface } from '../FlightData';

export default function RawData({
  data,
  role,
}: {
  data: RawDataInterface[];
  role: string;
}) {
  return (
    <div className="h-full flex flex-col">
      <h2>Raw Data</h2>
      <div className="flex flex-col overflow-auto">
        {data.length > 0 ? (
          data.map((dataset) => (
            <div key={dataset.id} className="flex flex-row items-center gap-4">
              Filename:
              <a
                className="text-sky-600 cursor-pointer"
                href={dataset.url}
                download={dataset.original_filename}
              >
                {dataset.original_filename}
              </a>
              {role !== 'viewer' ? (
                <div onClick={() => alert('not implemented')}>
                  <span className="sr-only">Delete {dataset.original_filename}</span>
                  <TrashIcon className="h-4 w-4 text-red-500 cursor-pointer" />
                </div>
              ) : null}
            </div>
          ))
        ) : (
          <span>No raw data has been uploaded</span>
        )}
      </div>
    </div>
  );
}
