import { isAxiosError } from 'axios';
import { useEffect, useState } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';

import RawDataDeleteModal from './RawDataDeleteModal';
import RawDataDownloadLink, { RawDataReportDownloadLink } from './RawDataDownloadLink';
import RawDataUploadModal from './RawDataUploadModal';
import { ErrorIcon, PendingIcon, ProgressIcon } from './RawDataStatusIcons';
import { useProjectContext } from '../../ProjectContext';
import { AlertBar, Status } from '../../../../Alert';
import { Button } from '../../../../Buttons';

import {
  ImageProcessingJobProps,
  ImageProcessingSettings,
  RawDataProps,
} from './RawData.types';

import {
  checkForExistingJobs,
  checkImageProcessingJobProgress,
  fetchUserExtensions,
  startImageProcessingJob,
} from './utils';
import { useInterval } from '../../../../hooks';
import ProgressBar from '../../../../ProgressBar';
import RawDataImageProcessingModal from './RawDataImageProcessingModal';

export default function RawData({ rawData }: { rawData: RawDataProps[] }) {
  const [hasImageProcessingExt, setHasImageProcessingExt] = useState(false);
  const [imageProcessingJobStatus, setImageProcessingJobStatus] = useState<
    ImageProcessingJobProps[]
  >([]);
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);

  const { flightId, projectId } = useParams();
  const revalidator = useRevalidator();

  const { projectRole } = useProjectContext();

  useEffect(() => {
    // check if user has image processing extension
    fetchUserExtensions()
      .then((hasExtension) => setHasImageProcessingExt(hasExtension))
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
  }, [projectRole]);

  useEffect(() => {
    // check for new raw data when upload modal closes
    if (!open) revalidator.revalidate();
  }, [open]);

  // check for new raw data and initial processing progress on regular intervals
  useInterval(
    () => {
      revalidator.revalidate();
    },
    rawData.length > 0 &&
      rawData.filter(({ status }) => status === 'INPROGRESS' || status === 'WAITING')
        .length > 0
      ? 5000 // check every 5 seconds while initial processing in progress
      : 30000 // check every 30 seconds for new raw data
  );

  // check for image processing job progress on regular interval once job begins
  useInterval(
    () => {
      if (flightId && projectId) {
        imageProcessingJobStatus.forEach((status) => {
          checkImageProcessingJobProgress(
            flightId,
            status.jobId,
            projectId,
            status.rawDataId
          )
            .then((progress) => {
              let updatedJobProgress = [...imageProcessingJobStatus];
              const jobIndex = updatedJobProgress.findIndex(
                (job) => job.rawDataId === status.rawDataId
              );
              if (jobIndex > -1) {
                if (progress === -9999) {
                  // job aborted or failed, remove job
                  updatedJobProgress.splice(jobIndex, 1);
                } else {
                  updatedJobProgress[jobIndex] = {
                    initialCheck: false,
                    jobId: status.jobId,
                    progress: progress || 0,
                    rawDataId: status.rawDataId,
                  };
                }
                setImageProcessingJobStatus(updatedJobProgress);
              }
            })
            .catch((err) => {
              if (isAxiosError(err) && err.response?.status === 404) {
                // check progress starts return 404 once batch id no longer exists
                // filter out any objects with job id for completed job (no batch id)
                setImageProcessingJobStatus(
                  imageProcessingJobStatus.filter((job) => job.jobId !== status.jobId)
                );
              }
            });
        });
      }
    },
    imageProcessingJobStatus.length > 0 ? 5000 : null
  );

  function onImageProcessingClick(
    rawDataId: string,
    settings: ImageProcessingSettings
  ) {
    if (flightId && projectId) {
      startImageProcessingJob(flightId, projectId, rawDataId, settings)
        .then((job_id) => {
          if (job_id) {
            setImageProcessingJobStatus([
              ...imageProcessingJobStatus,
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

  const isProcessing = (rawDataId: string): boolean =>
    imageProcessingJobStatus.findIndex((job) => job.rawDataId === rawDataId) > -1;

  const getProgressBarProps = (
    rawDataId: string
  ): { progress: number; initialCheck: boolean } => {
    const jobIndex = imageProcessingJobStatus.findIndex(
      (job) => job.rawDataId === rawDataId
    );
    if (jobIndex > -1) {
      const job = imageProcessingJobStatus[jobIndex];
      return { progress: job.progress, initialCheck: job.initialCheck };
    } else {
      return { progress: 0, initialCheck: false };
    }
  };

  return (
    <div className="h-full flex flex-col">
      <h2>Raw Data</h2>
      <div className="flex flex-col gap-2 overflow-auto">
        {rawData.length > 0 &&
          rawData.map((dataset) => (
            <div key={dataset.id} className="flex flex-row items-center gap-4">
              <div className="w-56 truncate">
                <span>Filename: {dataset.original_filename}</span>
              </div>
              <div className="flex items-center justify-between gap-4">
                {/* display icon for in progress or failed status */}
                {dataset.status === 'INPROGRESS' && <ProgressIcon />}
                {dataset.status === 'WAITING' && <PendingIcon />}
                {dataset.status === 'FAILED' && <ErrorIcon />}
                {/* display button for image processing if user has extension */}
                {hasImageProcessingExt && (
                  <RawDataImageProcessingModal
                    isProcessing={isProcessing(dataset.id)}
                    onSubmitJob={(settings: ImageProcessingSettings) =>
                      onImageProcessingClick(dataset.id, settings)
                    }
                  />
                )}
                {/* display button for downloading processed raw data zip file */}
                {dataset.status === 'SUCCESS' && (
                  <RawDataDownloadLink rawDataId={dataset.id} />
                )}
                {dataset.report && <RawDataReportDownloadLink url={dataset.report} />}
                {/* display button for removing processed raw data zip file */}
                {projectRole === 'owner' &&
                  (dataset.status === 'SUCCESS' || dataset.status === 'FAILED') && (
                    <RawDataDeleteModal rawData={dataset} iconOnly={true} />
                  )}
                {/* display progress for ongoing image processing jobs */}
                {isProcessing(dataset.id) && (
                  <ProgressBar
                    {...getProgressBarProps(dataset.id)}
                    completedMsg="Check Data Products tab for results"
                  />
                )}
              </div>
            </div>
          ))}
      </div>
      {/* display alert bar when status is not null */}
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
      {/* display upload button for project owners and managers */}
      {projectRole !== 'viewer' && projectId && flightId && (
        <div className="my-4 flex justify-center">
          <RawDataUploadModal
            flightID={flightId}
            open={open}
            projectID={projectId}
            setOpen={setOpen}
          />
          <Button size="sm" onClick={() => setOpen(true)}>
            Upload Raw Data
          </Button>
        </div>
      )}
    </div>
  );
}
