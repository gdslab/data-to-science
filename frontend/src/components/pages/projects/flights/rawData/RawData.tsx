import { useEffect } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';
import { ArrowDownTrayIcon, CogIcon } from '@heroicons/react/24/outline';

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

  const { projectId, flightId } = useParams();
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
              <span>Filename: {dataset.original_filename}</span>
              {dataset.status === 'SUCCESS' ? (
                <a
                  href={`${
                    import.meta.env.VITE_API_V1_STR
                  }/projects/${projectId}/flights/${flightId}/raw_data/${
                    dataset.id
                  }/download`}
                  download
                >
                  <span className="sr-only">Download</span>
                  <ArrowDownTrayIcon className="h-5 w-5 hover:scale-110" />
                </a>
              ) : (
                <div>
                  <span className="sr-only">Processing</span>
                  <CogIcon className="h-5 w-5 animate-spin" />
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
