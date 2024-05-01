import { useEffect } from 'react';
import { useRevalidator } from 'react-router-dom';
import { CogIcon } from '@heroicons/react/24/outline';

import { RawData as RawDataInterface } from '../FlightData';
import { useProjectContext } from '../../ProjectContext';
import RawDataDeleteModal from './RawDataDeleteModal';
import { useInterval } from '../../../../hooks';

export default function RawData({
  data,
  open,
}: {
  data: RawDataInterface[];
  open: boolean;
}) {
  const { projectRole } = useProjectContext();

  const revalidator = useRevalidator();

  useEffect(() => {
    if (!open) revalidator.revalidate();
  }, [open]);

  useInterval(
    () => {
      revalidator.revalidate();
    },
    data &&
      data.length > 0 &&
      data.filter(({ status }) => status === 'INPROGRESS').length > 0
      ? 30000 // 30 seconds
      : null
  );

  return (
    <div className="h-full flex flex-col">
      <h2>Raw Data</h2>
      <div className="flex flex-col overflow-auto">
        {data.length > 0 ? (
          data.map((dataset) => (
            <div key={dataset.id} className="flex flex-row items-center gap-4">
              Filename:
              {dataset.status === 'SUCCESS' ? (
                <a
                  className="text-sky-600 cursor-pointer"
                  href={dataset.url}
                  download={dataset.original_filename}
                >
                  {dataset.original_filename}
                </a>
              ) : (
                <div className="flex flex-row items-center gap-2">
                  <span>{dataset.original_filename}</span>
                  <CogIcon className="h-4 w-4 animate-spin" />
                  <span className="sr-only">Processing raw data</span>
                </div>
              )}
              {(projectRole === 'owner' && dataset.status === 'SUCCESS') ||
              dataset.status === 'FAILED' ? (
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
