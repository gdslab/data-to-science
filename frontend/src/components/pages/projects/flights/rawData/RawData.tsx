import { useEffect, useState } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';
import {
  ArrowDownTrayIcon,
  ClockIcon,
  CogIcon,
  ExclamationTriangleIcon,
  Square3Stack3DIcon,
} from '@heroicons/react/24/outline';

import { RawData as RawDataInterface } from '../FlightData';
import { useProjectContext } from '../../ProjectContext';
import RawDataDeleteModal from './RawDataDeleteModal';
import { useInterval } from '../../../../hooks';
import axios, { AxiosResponse, isAxiosError } from 'axios';
import { AlertBar, Status } from '../../../../Alert';

export default function RawData({
  data,
  open,
}: {
  data: RawDataInterface[];
  open: boolean;
}) {
  const [extensions, setExtensions] = useState<string[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const { projectRole } = useProjectContext();

  const { projectId, flightId } = useParams();
  const revalidator = useRevalidator();

  useEffect(() => {
    async function fetchUserExtensions() {
      try {
        const response: AxiosResponse<string[]> = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/users/extensions`
        );
        if (response.status === 200) {
          setExtensions(response.data);
        } else {
          console.log('Unable to fetch user');
        }
      } catch (err) {
        if (isAxiosError(err) && err.response && err.response.data.detail) {
          console.error(err.response.data.detail);
        } else {
          console.error('Unable to fetch user');
        }
      }
    }
    fetchUserExtensions();
  }, []);

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

  function processRawData(rawDataId: string) {
    async function startProcessingJob() {
      try {
        const response = await axios.get(
          `${
            import.meta.env.VITE_API_V1_STR
          }/projects/${projectId}/flights/${flightId}/raw_data/${rawDataId}/process`
        );
        if (response.status === 200) {
          setStatus({
            type: 'success',
            msg: `Raw data processing job for ${rawDataId} started at ${new Date().toLocaleTimeString()}`,
          });
        } else {
          setStatus({ type: 'error', msg: 'Unable to start job' });
        }
      } catch (err) {
        if (isAxiosError(err) && err.response && err.response.data.detail) {
          setStatus({ type: 'error', msg: err.response.data.detail });
        } else {
          setStatus({ type: 'error', msg: 'Unable to start job' });
        }
      }
    }

    if (projectId && flightId && rawDataId) {
      startProcessingJob();
    }
  }

  return (
    <div className="h-full flex flex-col">
      <h2>Raw Data</h2>
      <div className="flex flex-col overflow-auto">
        {data.length > 0 ? (
          data.map((dataset) => (
            <div key={dataset.id} className="flex flex-row items-center gap-4">
              <div className="w-56 truncate">
                <span>Filename: {dataset.original_filename}</span>
              </div>
              <div className="flex justify-between gap-4">
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
                ) : dataset.status === 'INPROGRESS' ? (
                  <div>
                    <span className="sr-only">Processing</span>
                    <CogIcon className="h-5 w-5 animate-spin" />
                  </div>
                ) : dataset.status === 'PENDING' ? (
                  <div>
                    <span className="sr-only">Pending</span>
                    <ClockIcon className="h-5 w-5" />
                  </div>
                ) : (
                  <div>
                    <span className="sr-only">Failed</span>
                    <ExclamationTriangleIcon
                      className="h-5 w-5 text-red-600"
                      title="Processing failed"
                    />
                  </div>
                )}
                {extensions.indexOf('cluster') > -1 && (
                  <button
                    type="button"
                    name="processRawDataBtn"
                    onClick={() => processRawData(dataset.id)}
                  >
                    <span className="sr-only">Process</span>
                    <Square3Stack3DIcon className="h-5 w-5" />
                  </button>
                )}
                {(projectRole === 'owner' && dataset.status === 'SUCCESS') ||
                dataset.status === 'FAILED' ? (
                  <RawDataDeleteModal rawData={dataset} iconOnly={true} />
                ) : null}
              </div>
            </div>
          ))
        ) : (
          <span>No raw data has been uploaded</span>
        )}
      </div>
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </div>
  );
}
