import { RawData as RawDataInterface } from '../FlightData';
import { useProjectContext } from '../../ProjectContext';
import RawDataDeleteModal from './RawDataDeleteModal';

export default function RawData({ data }: { data: RawDataInterface[] }) {
  const { projectRole } = useProjectContext();

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
              {projectRole === 'owner' ? (
                <RawDataDeleteModal rawData={dataset} iconOnly={true} />
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
