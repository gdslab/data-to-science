import { isAxiosError } from 'axios';
import { useEffect, useState } from 'react';
import { useParams, useRevalidator } from 'react-router';

import { AlertBar, Status } from '../../../../../Alert';
import { Button } from '../../../../../Buttons';
import LoadingBars from '../../../../../LoadingBars';
import RawDataCard from './RawDataCard';
import RawDataUploadModal from './RawDataUploadModal';

import { useInterval } from '../../../../../hooks';
import { useProjectContext } from '../../ProjectContext';
import {
  ImageProcessingBackend,
  ImageProcessingJobProps,
  MetashapeSettings,
  ODMSettings,
  RawDataProps,
} from './RawData.types';

import {
  checkForExistingJobs,
  checkImageProcessingJobProgress,
  fetchUserExtensions,
  startImageProcessingJob,
} from './utils';

export default function RawData({ rawData }: { rawData: RawDataProps[] }) {
  const [imageProcessingExts, setImageProcessingExts] = useState<
    ImageProcessingBackend[]
  >([]);
  const [imageProcessingJobStatus, setImageProcessingJobStatus] = useState<
    ImageProcessingJobProps[]
  >([]);
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const { flightId, projectId } = useParams();
  const revalidator = useRevalidator();

  const { projectRole } = useProjectContext();

  useEffect(() => {
    // check if user has image processing extension
    fetchUserExtensions()
      .then((extensions) => setImageProcessingExts(extensions))
      .catch((err) => setStatus({ type: 'error', msg: err.message }));
  }, []);

  useEffect(() => {
    // check for any outstanding image processing jobs on initial render
    if (flightId && projectId && projectRole && projectRole !== 'viewer') {
      checkForExistingJobs(flightId, projectId)
        .then((jobs) => {
          const jobProgress: ImageProcessingJobProps[] = jobs.map((job) => ({
            initialCheck: true,
            jobId: job.id,
            progress: 0,
            rawDataId: job.raw_data_id,
          }));
          setImageProcessingJobStatus(jobProgress);
        })
        .catch((err) => setStatus({ type: 'error', msg: err.message }));
    }
  }, [flightId, projectId, projectRole]);

  function handleModalClose() {
    setOpen(false);
    revalidator.revalidate(); // Revalidate when modal closes
  }

  // check for new raw data and initial processing progress on regular intervals
  useInterval(
    () => {
      revalidator.revalidate();
    },
    rawData.length > 0 &&
      rawData.filter(
        ({ status }) => status === 'INPROGRESS' || status === 'WAITING'
      ).length > 0
      ? 5000 // check every 5 seconds while initial processing in progress
      : 30000 // check every 30 seconds for new raw data
  );

  const markJobFailed = (jobId: string) =>
    setImageProcessingJobStatus((prev) =>
      prev.map((job) => (job.jobId === jobId ? { ...job, failed: true } : job))
    );

  // check for image processing job progress on regular interval once job begins
  useInterval(
    () => {
      if (flightId && projectId) {
        imageProcessingJobStatus
          .filter((job) => !job.failed)
          .forEach((jobStatus) => {
            checkImageProcessingJobProgress(
              flightId,
              jobStatus.jobId,
              projectId,
              jobStatus.rawDataId
            )
              .then((result) => {
                if (!result) return;
                if (result.status === 'FAILED') {
                  markJobFailed(jobStatus.jobId);
                } else if (result.status === 'SUCCESS') {
                  // run finished; drop the entry so polling stops and the
                  // card switches to the refreshed latest-run summary
                  setImageProcessingJobStatus((prev) =>
                    prev.filter((job) => job.jobId !== jobStatus.jobId)
                  );
                  revalidator.revalidate();
                } else {
                  setImageProcessingJobStatus((prev) =>
                    prev.map((job) =>
                      job.jobId === jobStatus.jobId
                        ? {
                            ...job,
                            initialCheck: false,
                            progress: result.progress,
                          }
                        : job
                    )
                  );
                }
              })
              .catch((err) => {
                if (isAxiosError(err) && err.response?.status === 404) {
                  // job no longer exists; remove entry and refresh list
                  setImageProcessingJobStatus((prev) =>
                    prev.filter((job) => job.jobId !== jobStatus.jobId)
                  );
                  revalidator.revalidate();
                }
                // transient errors: skip this tick and retry on the next
              });
          });
      }
    },
    imageProcessingJobStatus.filter((job) => !job.failed).length > 0
      ? 15000
      : null
  );

  useEffect(() => {
    if (projectRole !== undefined) {
      setIsLoading(false);
    }
  }, [projectRole]);

  function onImageProcessingClick(
    rawDataId: string,
    settings: MetashapeSettings | ODMSettings
  ) {
    if (flightId && projectId) {
      startImageProcessingJob(flightId, projectId, rawDataId, settings)
        .then((job_id) => {
          if (job_id) {
            setImageProcessingJobStatus((prev) => [
              // replace any dismissed/failed entry for this raw data
              ...prev.filter((job) => job.rawDataId !== rawDataId),
              {
                initialCheck: false,
                jobId: job_id,
                progress: 0,
                rawDataId: rawDataId,
              },
            ]);
          }
        })
        .catch((err) => setStatus({ type: 'error', msg: err.message }));
    }
  }

  function onDismissFailedJob(rawDataId: string) {
    setImageProcessingJobStatus((prev) =>
      prev.filter((job) => !(job.rawDataId === rawDataId && job.failed))
    );
  }

  if (isLoading) {
    return <LoadingBars />;
  }

  return (
    <div className="h-full flex flex-col">
      <h2>Raw Data</h2>

      <div className="overflow-auto">
        {rawData.length === 0 ? (
          <p className="text-gray-600">No raw data uploaded yet.</p>
        ) : (
          <div className="flex flex-wrap gap-4">
            {rawData.map((dataset) => (
              <RawDataCard
                key={dataset.id}
                rawData={dataset}
                imageProcessingExts={imageProcessingExts}
                activeJob={imageProcessingJobStatus.find(
                  (job) => job.rawDataId === dataset.id
                )}
                onDismissFailedJob={onDismissFailedJob}
                onImageProcessingClick={onImageProcessingClick}
              />
            ))}
          </div>
        )}
      </div>

      {/* display alert bar when status is not null */}
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
      {/* display upload button for project owners and managers */}
      {projectRole && projectRole !== 'viewer' && projectId && flightId && (
        <div className="my-4 flex justify-center">
          <RawDataUploadModal
            flightID={flightId}
            open={open}
            projectID={projectId}
            handleModalClose={handleModalClose}
          />
          <Button size="sm" onClick={() => setOpen(true)}>
            Upload Raw Data
          </Button>
        </div>
      )}
    </div>
  );
}
