import { Fragment } from 'react';
import {
  CheckCircleIcon,
  ClockIcon,
  CogIcon,
  QuestionMarkCircleIcon,
  XCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import ProgressBar from '../../../../../ProgressBar';
import RawDataDeleteModal from './RawDataDeleteModal';
import RawDataDownloadLink, {
  RawDataReportDownloadLink,
} from './RawDataDownloadLink';
import RawDataImageProcessingModal from './RawDataImageProcessingModal';
import RawDataProcessingHistoryModal from './RawDataProcessingHistoryModal';
import Table, { Action, TableBody, TableHead } from '../../../../../Table';
import { useProjectContext } from '../../ProjectContext';

import {
  ImageProcessingBackend,
  ImageProcessingJobProps,
  MetashapeSettings,
  ODMSettings,
  RawDataProps,
} from './RawData.types';

function UploadStatus({ status }: { status: RawDataProps['status'] }) {
  if (status === 'WAITING') {
    return (
      <Fragment>
        <ClockIcon className="h-6 w-6 mr-2" aria-hidden="true" />
        Queued
      </Fragment>
    );
  }
  if (status === 'INPROGRESS') {
    return (
      <Fragment>
        <CogIcon className="h-6 w-6 mr-2 animate-spin" aria-hidden="true" />
        Extracting
      </Fragment>
    );
  }
  if (status === 'SUCCESS') {
    return (
      <Fragment>
        <CheckCircleIcon className="h-6 w-6 mr-2 text-green-500" /> Ready
      </Fragment>
    );
  }
  if (status === 'FAILED') {
    return (
      <Fragment>
        <XCircleIcon className="h-6 w-6 mr-2 text-red-500" /> Upload failed
      </Fragment>
    );
  }
  return (
    <Fragment>
      <QuestionMarkCircleIcon className="h-6 w-6 mr-2" /> Unknown
    </Fragment>
  );
}

export default function RawDataTable({
  rawData,
  imageProcessingExts,
  imageProcessingJobStatus,
  onDismissFailedJob,
  onImageProcessingClick,
}: {
  rawData: RawDataProps[];
  imageProcessingExts: ImageProcessingBackend[];
  imageProcessingJobStatus: ImageProcessingJobProps[];
  onDismissFailedJob: (rawDataId: string) => void;
  onImageProcessingClick: (
    rawDataId: string,
    settings: MetashapeSettings | ODMSettings
  ) => void;
}) {
  const { projectRole } = useProjectContext();

  const getJob = (rawDataId: string): ImageProcessingJobProps | undefined =>
    imageProcessingJobStatus.find((job) => job.rawDataId === rawDataId);

  const getActions = (dataset: RawDataProps): Action[] => {
    const actions: Action[] = [];
    const job = getJob(dataset.id);
    if (imageProcessingExts.length > 0 && projectRole !== 'viewer') {
      actions.push({
        key: `action-process-${dataset.id}`,
        type: 'component',
        component: (
          <RawDataImageProcessingModal
            imageProcessingExts={imageProcessingExts}
            isProcessing={Boolean(job && !job.failed)}
            onSubmitJob={(settings: MetashapeSettings | ODMSettings) =>
              onImageProcessingClick(dataset.id, settings)
            }
          />
        ),
        label: 'Process',
      });
    }
    if (dataset.status === 'SUCCESS') {
      actions.push({
        key: `action-download-${dataset.id}`,
        type: 'component',
        component: <RawDataDownloadLink rawDataId={dataset.id} />,
        label: 'Download',
      });
    }
    if (dataset.report) {
      actions.push({
        key: `action-report-${dataset.id}`,
        type: 'component',
        component: <RawDataReportDownloadLink url={dataset.report} />,
        label: 'Report',
      });
    }
    actions.push({
      key: `action-history-${dataset.id}`,
      type: 'component',
      component: <RawDataProcessingHistoryModal rawData={dataset} />,
      label: 'History',
    });
    if (
      projectRole === 'owner' &&
      (dataset.status === 'SUCCESS' || dataset.status === 'FAILED')
    ) {
      actions.push({
        key: `action-delete-${dataset.id}`,
        type: 'component',
        component: <RawDataDeleteModal rawData={dataset} tableView={true} />,
        label: 'Delete',
      });
    }
    return actions;
  };

  if (rawData.length === 0) {
    return (
      <p className="text-gray-600">No raw data uploaded yet.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[800px]">
        <Table>
          <TableHead columns={['Filename', 'Upload Status', 'Processing', 'Action']} />
          <TableBody
            rows={rawData.map((dataset) => {
              const job = getJob(dataset.id);
              return {
                key: dataset.id,
                values: [
                  <div
                    key={`row-${dataset.id}-filename`}
                    className="w-full truncate"
                    title={dataset.original_filename}
                  >
                    {dataset.original_filename}
                  </div>,
                  <div
                    key={`row-${dataset.id}-status`}
                    className="flex items-center"
                  >
                    <UploadStatus status={dataset.status} />
                  </div>,
                  <div
                    key={`row-${dataset.id}-processing`}
                    className="flex items-center"
                  >
                    {job && job.failed ? (
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                        Processing failed &mdash; see History
                        <button
                          className="cursor-pointer"
                          type="button"
                          title="Dismiss"
                          onClick={() => onDismissFailedJob(dataset.id)}
                        >
                          <span className="sr-only">Dismiss</span>
                          <XMarkIcon className="h-3.5 w-3.5" />
                        </button>
                      </span>
                    ) : job ? (
                      <ProgressBar
                        progress={job.progress}
                        initialCheck={job.initialCheck}
                        completedMsg="Check Data Products tab for results"
                      />
                    ) : (
                      <span className="text-gray-400">&mdash;</span>
                    )}
                  </div>,
                ],
              };
            })}
            actions={rawData.map((dataset) => getActions(dataset))}
          />
        </Table>
      </div>
    </div>
  );
}
