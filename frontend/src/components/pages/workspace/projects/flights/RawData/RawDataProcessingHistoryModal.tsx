import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { ClockIcon } from '@heroicons/react/24/outline';

import { AlertBar } from '../../../../../Alert';
import LoadingBars from '../../../../../LoadingBars';
import Modal from '../../../../../Modal';
import StripedTable from '../../../../../StripedTable';
import { RawDataReportDownloadLink } from './RawDataDownloadLink';

import { ProcessingJob, RawDataProps } from './RawData.types';
import {
  fetchRawDataProcessingJobs,
  formatDuration,
  formatSettingKey,
  formatSettingValue,
} from './utils';

function ProcessingJobStatusPill({ job }: { job: ProcessingJob }) {
  if (job.status === 'WAITING' || job.status === 'INPROGRESS') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
        <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500"></span>
        Processing...
      </span>
    );
  }
  if (job.status === 'FAILED') {
    return (
      <span
        className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800"
        title={job.extra?.detail || 'Processing failed'}
      >
        Failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
      Success
    </span>
  );
}

function ProcessingJobSettings({ job }: { job: ProcessingJob }) {
  const settings = job.extra?.settings;
  if (!settings || Object.keys(settings).length === 0) {
    return (
      <span className="text-sm italic text-gray-400">
        Settings not recorded
      </span>
    );
  }

  const entries = Object.entries(settings);
  const summary = entries
    .slice(0, 3)
    .map(
      ([key, value]) => `${formatSettingKey(key)}: ${formatSettingValue(value)}`
    )
    .join(' · ');

  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm text-gray-600">
        {summary}
        {entries.length > 3 ? ' · …' : ''}
      </span>
      {entries.length > 3 && (
        <details>
          <summary className="cursor-pointer text-sm text-sky-600">
            Show all settings
          </summary>
          <div className="mt-2 max-h-64 overflow-y-auto rounded border border-gray-200">
            <StripedTable
              headers={['Setting', 'Value']}
              values={entries.map(([key, value]) => ({
                label: formatSettingKey(key),
                value: formatSettingValue(value),
              }))}
            />
          </div>
        </details>
      )}
    </div>
  );
}

export default function RawDataProcessingHistoryModal({
  rawData,
}: {
  rawData: RawDataProps;
}) {
  const [open, setOpen] = useState(false);
  const [jobs, setJobs] = useState<ProcessingJob[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { flightId, projectId } = useParams();

  useEffect(() => {
    if (open && flightId && projectId) {
      setJobs(null);
      setError(null);
      fetchRawDataProcessingJobs(projectId, flightId, rawData.id)
        .then((fetchedJobs) => setJobs(fetchedJobs))
        .catch((err) => setError(err.message));
    }
  }, [open, flightId, projectId, rawData.id]);

  // legacy runs share a single report.pdf that belongs to the latest
  // successful run; newer runs carry their own report URL in extra
  const latestSuccessJobId = jobs?.find((job) => job.status === 'SUCCESS')?.id;

  return (
    <div>
      <button
        className="flex items-center gap-1 text-sky-600 cursor-pointer"
        type="button"
        title="View processing history for this raw data"
        onClick={() => setOpen(true)}
      >
        <ClockIcon className="w-4 h-4" />
        <span className="text-sm">History</span>
      </button>
      <Modal open={open} setOpen={setOpen}>
        <div className="p-6">
          <h3 className="mb-1">Processing History</h3>
          <p className="mb-4 text-sm text-gray-600 truncate">
            {rawData.original_filename}
          </p>
          {error ? (
            <AlertBar alertType="error">{error}</AlertBar>
          ) : !jobs ? (
            <LoadingBars />
          ) : jobs.length === 0 ? (
            <p className="text-sm text-gray-600">No processing runs yet.</p>
          ) : (
            <ul className="flex flex-col gap-2 max-h-[60vh] overflow-y-auto">
              {jobs.map((job) => (
                <li
                  key={job.id}
                  className="rounded border border-gray-200 p-3 flex flex-col gap-2"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <ProcessingJobStatusPill job={job} />
                    <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                      {job.extra?.backend === 'metashape'
                        ? 'Metashape'
                        : job.extra?.backend === 'odm'
                        ? 'ODM'
                        : 'Unknown backend'}
                    </span>
                    <span className="text-xs text-gray-400">
                      Started {new Date(job.start_time).toLocaleString()}
                    </span>
                    <span className="text-xs text-gray-400">
                      {job.end_time && job.state === 'COMPLETED'
                        ? `Duration ${formatDuration(
                            job.start_time,
                            job.end_time
                          )}`
                        : 'Running'}
                    </span>
                    {job.status === 'SUCCESS' &&
                      (job.extra?.report ? (
                        <RawDataReportDownloadLink url={job.extra.report} />
                      ) : (
                        rawData.report &&
                        job.id === latestSuccessJobId && (
                          <RawDataReportDownloadLink url={rawData.report} />
                        )
                      ))}
                  </div>
                  {job.status === 'FAILED' && job.extra?.detail && (
                    <span className="text-sm text-red-700">
                      {job.extra.detail}
                    </span>
                  )}
                  <ProcessingJobSettings job={job} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </Modal>
    </div>
  );
}
