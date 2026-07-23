import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { FaXmark } from 'react-icons/fa6';

import Card from '../../../../../Card';
import ProgressBar from '../../../../../ProgressBar';
import RawDataDeleteModal from './RawDataDeleteModal';
import RawDataDownloadLink, {
  RawDataReportDownloadLink,
} from './RawDataDownloadLink';
import RawDataImageProcessingModal from './RawDataImageProcessingModal';
import RawDataProcessingHistoryModal, {
  ProcessingJobStatusPill,
} from './RawDataProcessingHistoryModal';
import { useProjectContext } from '../../ProjectContext';

import {
  ImageProcessingBackend,
  ImageProcessingJobProps,
  MetashapeSettings,
  ODMSettings,
  ProcessingJob,
  RawDataProps,
} from './RawData.types';
import { fetchRawDataProcessingJobs } from './utils';

function UploadStatusPill({ status }: { status: RawDataProps['status'] }) {
  if (status === 'SUCCESS') {
    return (
      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
        Ready
      </span>
    );
  }
  if (status === 'WAITING') {
    return (
      <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
        Queued
      </span>
    );
  }
  if (status === 'INPROGRESS') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
        <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500"></span>
        Extracting
      </span>
    );
  }
  if (status === 'FAILED') {
    return (
      <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
        Upload failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
      Unknown
    </span>
  );
}

export default function RawDataCard({
  rawData,
  imageProcessingExts,
  activeJob,
  onDismissFailedJob,
  onImageProcessingClick,
}: {
  rawData: RawDataProps;
  imageProcessingExts: ImageProcessingBackend[];
  activeJob: ImageProcessingJobProps | undefined;
  onDismissFailedJob: (rawDataId: string) => void;
  onImageProcessingClick: (
    rawDataId: string,
    settings: MetashapeSettings | ODMSettings
  ) => void;
}) {
  const [jobs, setJobs] = useState<ProcessingJob[] | null>(null);

  const { flightId, projectId } = useParams();
  const { projectRole } = useProjectContext();

  const isProcessing = Boolean(activeJob && !activeJob.failed);

  useEffect(() => {
    // load latest run summary on mount and again when a run finishes
    if (!isProcessing && flightId && projectId) {
      fetchRawDataProcessingJobs(projectId, flightId, rawData.id)
        .then((fetchedJobs) => setJobs(fetchedJobs))
        .catch((err) => console.error(err));
    }
  }, [rawData.id, isProcessing, flightId, projectId]);

  const latestRun = jobs && jobs.length > 0 ? jobs[0] : null;
  const latestRunReport = latestRun
    ? latestRun.extra?.report ||
      (latestRun.status === 'SUCCESS' ? rawData.report : undefined)
    : undefined;

  const showDownload = rawData.status === 'SUCCESS';
  const showDelete =
    projectRole === 'owner' &&
    (rawData.status === 'SUCCESS' || rawData.status === 'FAILED');

  return (
    <div className="min-w-0 w-full sm:w-96">
      <Card rounded={true}>
        {/* min-w-0 at every level so the filename truncates instead of
            stretching the card */}
        <div className="min-w-0 grid grid-flow-row auto-rows-max gap-3">
          {/* filename and upload status */}
          <div className="min-w-0 flex items-center justify-between gap-2">
            <span
              className="min-w-0 flex-1 font-semibold truncate"
              title={rawData.original_filename}
            >
              {rawData.original_filename}
            </span>
            <span className="shrink-0">
              <UploadStatusPill status={rawData.status} />
            </span>
          </div>

          {/* processing section; fixed-height status slot keeps card heights
              consistent across processing states */}
          <div className="flex flex-col gap-2">
            <div className="min-h-6 flex items-center">
              {activeJob && activeJob.failed ? (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                  Processing failed &mdash; see History
                  <button
                    className="cursor-pointer"
                    type="button"
                    title="Dismiss"
                    onClick={() => onDismissFailedJob(rawData.id)}
                  >
                    <span className="sr-only">Dismiss</span>
                    <FaXmark className="h-3.5 w-3.5" />
                  </button>
                </span>
              ) : activeJob && activeJob.progress >= 100 ? (
                <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                  Done &mdash; check Data Products tab for results
                </span>
              ) : activeJob ? (
                <ProgressBar
                  progress={activeJob.progress}
                  initialCheck={activeJob.initialCheck}
                />
              ) : latestRun ? (
                <div className="flex flex-wrap items-center gap-2">
                  <ProcessingJobStatusPill job={latestRun} />
                  <span className="text-xs text-gray-400">
                    {new Date(latestRun.start_time).toLocaleDateString()}
                  </span>
                  {latestRunReport && (
                    <RawDataReportDownloadLink url={latestRunReport} />
                  )}
                </div>
              ) : (
                <span className="text-sm italic text-gray-400">
                  Not processed yet
                </span>
              )}
            </div>
            <div className="flex gap-2">
              {imageProcessingExts.length > 0 && projectRole !== 'viewer' && (
                <div className="w-32">
                  <RawDataImageProcessingModal
                    imageProcessingExts={imageProcessingExts}
                    isProcessing={isProcessing}
                    onSubmitJob={(settings: MetashapeSettings | ODMSettings) =>
                      onImageProcessingClick(rawData.id, settings)
                    }
                  />
                </div>
              )}
              <div className="w-32">
                <RawDataProcessingHistoryModal rawData={rawData} />
              </div>
            </div>
          </div>

          {/* zip file actions */}
          {(showDownload || showDelete) && (
            <div className="border-t border-gray-100 pt-3 flex items-center justify-between">
              {showDownload ? (
                <RawDataDownloadLink rawDataId={rawData.id} />
              ) : (
                <span />
              )}
              {showDelete && (
                <RawDataDeleteModal rawData={rawData} tableView={true} />
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
