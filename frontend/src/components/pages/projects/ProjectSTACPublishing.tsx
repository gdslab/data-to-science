import { isAxiosError } from 'axios';
import { useState } from 'react';
import {
  GlobeAmericasIcon,
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

import api from '../../../api';
import { confirm } from '../../ConfirmationDialog';

// Types based on the backend schema
interface STACError {
  code: string;
  message: string;
  timestamp: string;
  details?: Record<string, any>;
}

interface ItemStatus {
  item_id: string;
  is_published: boolean;
  item_url?: string;
  error?: STACError;
}

interface STACReport {
  collection_id: string;
  items: ItemStatus[];
  is_published: boolean;
  collection_url?: string;
  error?: STACError;
}

interface PublishingReportProps {
  report: STACReport;
  onClose: () => void;
}

function PublishingReport({ report, onClose }: PublishingReportProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Publishing Report</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl font-bold"
          >
            ×
          </button>
        </div>

        {report.error ? (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center">
              <XCircleIcon className="h-5 w-5 text-red-600 mr-2" />
              <span className="text-red-800 font-medium">
                Collection Error:
              </span>
            </div>
            <p className="text-red-700 mt-1">{report.error.message}</p>
          </div>
        ) : null}

        <div className="space-y-2">
          {report.items.map((item, index) => (
            <div
              key={item.item_id}
              className="flex items-center justify-between p-3 border border-gray-200 rounded-md"
            >
              <div className="flex items-center flex-1">
                <span className="text-gray-700 mr-3">Item {index + 1}</span>
                <div className="flex-1 border-b border-dotted border-gray-300 mx-2"></div>
              </div>

              <div className="flex items-center">
                {item.is_published ? (
                  <div className="flex items-center text-green-600">
                    <CheckCircleIcon className="h-5 w-5 mr-1" />
                    <span className="font-medium">Success</span>
                  </div>
                ) : (
                  <div className="flex items-center text-red-600">
                    <XCircleIcon className="h-5 w-5 mr-1" />
                    <span className="font-medium">Failed</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {report.items
            .filter((item) => !item.is_published && item.error)
            .map((item, index) => (
              <div
                key={`error-${item.item_id}`}
                className="ml-4 p-2 bg-red-50 border-l-4 border-red-400 text-sm"
              >
                <p className="text-red-700">
                  <strong>Error:</strong> {item.error?.message}
                </p>
              </div>
            ))}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ProjectSTACPublishing({
  is_published,
  projectId,
  setStatus,
}: {
  is_published: boolean;
  projectId: string;
  setStatus: (status: { type: string; msg: string }) => void;
}) {
  const [publishingReport, setPublishingReport] = useState<STACReport | null>(
    null
  );

  const handleOnPublish = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (
      await confirm({
        title: 'Publish to STAC',
        description:
          'You are about to publish this project to a public STAC catalog. This action will make all data products associated with this project <strong>publicly available</strong>.',
        confirmation: 'Are you sure you want to publish this project to STAC?',
      })
    ) {
      try {
        const response = await api.put(`/projects/${projectId}/publish-stac`);
        if (response?.data) {
          const report: STACReport = response.data;
          setPublishingReport(report);

          // Also set the traditional status message
          const successCount = report.items.filter(
            (item) => item.is_published
          ).length;
          const totalCount = report.items.length;

          if (successCount === totalCount) {
            setStatus({
              type: 'success',
              msg: `${totalCount} data products published successfully`,
            });
          } else {
            setStatus({
              type: 'warning',
              msg: `${successCount} of ${totalCount} data products published successfully`,
            });
          }
        }
      } catch (error) {
        if (isAxiosError(error)) {
          setStatus({ type: 'error', msg: error.response?.data.detail });
        } else {
          setStatus({
            type: 'error',
            msg: 'An error occurred while publishing the project to STAC',
          });
        }
      }
    }
  };

  const handleOnDelete = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (
      await confirm({
        title: 'Remove from STAC',
        description:
          'You are about to remove this project from the public STAC catalog. This action will make all data products associated with this project <strong>private</strong>.',
        confirmation: 'Are you sure you want to remove this project from STAC?',
      })
    ) {
      try {
        const response = await api.delete(`/projects/${projectId}/delete-stac`);
        if (response) {
          setStatus({ type: 'success', msg: 'Project removed from STAC' });
        }
      } catch (error) {
        if (isAxiosError(error)) {
          setStatus({ type: 'error', msg: error.response?.data.detail });
        } else {
          setStatus({
            type: 'error',
            msg: 'An error occurred while removing the project from STAC',
          });
        }
      }
    }
  };

  return (
    <>
      {publishingReport && (
        <PublishingReport
          report={publishingReport}
          onClose={() => setPublishingReport(null)}
        />
      )}

      {is_published ? (
        <div className="flex flex-col items-center gap-2">
          <button
            className="w-32 flex flex-row items-center gap-2 py-0.5 px-2 border-2 rounded-md text-white ease-in-out duration-300 bg-[#4eb4ae] hover:bg-[#4eb4ae]/80 border-[#4eb4ae] hover:border-[#4eb4ae]/80"
            onClick={handleOnPublish}
          >
            <EyeIcon className="h-6 w-6" />
            <span className="text-sm font-semibold">Update</span>
          </button>
          <button
            className="w-32 flex flex-row items-center gap-2 py-0.5 px-2 border-2 rounded-md text-white ease-in-out duration-300 bg-red-600 hover:bg-red-700 border-red-600 hover:border-red-700"
            onClick={handleOnDelete}
          >
            <EyeSlashIcon className="h-6 w-6" />
            <span className="text-sm font-semibold">Unpublish</span>
          </button>
        </div>
      ) : (
        <button
          className="w-32 flex flex-row items-center gap-2 py-0.5 px-2 border-2 rounded-md text-white ease-in-out duration-300 bg-[#4eb4ae] hover:bg-[#4eb4ae]/80 border-[#4eb4ae] hover:border-[#4eb4ae]/80"
          onClick={handleOnPublish}
        >
          <GlobeAmericasIcon className="h-6 w-6" />
          <span className="text-sm font-semibold">Publish</span>
        </button>
      )}
    </>
  );
}
