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

function ProgressBar({ progress }: { progress: number }) {
  return (
    <div className="w-60">
      <div className="w-full bg-gray-400 rounded-full">
        <div
          className="bg-blue-600 text-xs font-medium text-blue-100 text-center p-0.5 leading-none rounded-full"
          style={{ width: progress === 0 ? undefined : `${Math.ceil(progress)}%` }}
        >
          {progress === 0 ? 'PENDING' : `${Math.ceil(progress)}%`}
        </div>
      </div>
    </div>
  );
}

export default function RawData({
  data,
  open,
}: {
  data: RawDataInterface[];
  open: boolean;
}) {
  const [extensions, setExtensions] = useState<string[]>([]);
  const [jobIds, setJobIds] = useState<{ rawDataId: string; jobId: string }[]>([]);
  const [jobProgress, setJobProgress] = useState<
    { rawDataId: string; progress: number }[]
  >([]);
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

  // check for raw data processing progress
  useInterval(
    () => {
      jobIds.forEach((job) => {
        checkProgress(job.rawDataId, job.jobId);
      });
    },
    jobIds.length > 0 ? 5000 : null
  );

  async function checkProgress(rawDataId: string, jobId: string) {
    try {
      const response: AxiosResponse<{ progress: number }> = await axios.get(
        `${
          import.meta.env.VITE_API_V1_STR
        }/projects/${projectId}/flights/${flightId}/raw_data/${rawDataId}/check_progress/${jobId}`
      );
      if (response.status === 200) {
        let updatedJobProgress = [...jobProgress];
        const rawDataProgressIndex = updatedJobProgress.findIndex(
          (progress) => progress.rawDataId === rawDataId
        );
        if (rawDataProgressIndex > -1) {
          updatedJobProgress[rawDataProgressIndex] = {
            rawDataId: rawDataId,
            progress: response.data.progress,
          };
          setJobProgress(updatedJobProgress);
        }
      }
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 404) {
        // remove job from progress and id tracker
        let updatedJobProgress = [...jobProgress];
        const rawDataProgressIndex = updatedJobProgress.findIndex(
          (progress) => progress.rawDataId === rawDataId
        );
        if (rawDataProgressIndex > -1) {
          updatedJobProgress.splice(rawDataProgressIndex, 1);
          setJobProgress(updatedJobProgress);
        }
        let updatedJobIds = [...jobIds];
        const jobIdsIndex = updatedJobIds.findIndex((job) => job.jobId === jobId);
        if (jobIdsIndex > -1) {
          updatedJobIds.splice(jobIdsIndex, 1);
          setJobIds(updatedJobIds);
        }
        revalidator.revalidate();
      }
    }
  }

  function processRawData(rawDataId: string) {
    async function startProcessingJob() {
      try {
        const response: AxiosResponse<{ job_id: string }> = await axios.get(
          `${
            import.meta.env.VITE_API_V1_STR
          }/projects/${projectId}/flights/${flightId}/raw_data/${rawDataId}/process`
        );
        if (response.status === 200) {
          setJobProgress([...jobProgress, { rawDataId: rawDataId, progress: 0 }]);
          setJobIds([
            ...jobIds,
            {
              rawDataId: rawDataId,
              jobId: response.data.job_id,
            },
          ]);
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
                {extensions.indexOf('image_processing') > -1 && (
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
                {jobProgress.findIndex(
                  (job) => job.rawDataId === dataset.id && job.progress < 100
                ) > -1 && (
                  <ProgressBar
                    progress={
                      jobProgress[
                        jobProgress.findIndex(
                          (job) => job.rawDataId === dataset.id && job.progress < 100
                        )
                      ].progress
                    }
                  />
                )}
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
