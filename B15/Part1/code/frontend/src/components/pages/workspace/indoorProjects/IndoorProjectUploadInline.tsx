import '@uppy/core/css/style.min.css';
import '@uppy/dashboard/css/style.min.css';

import { useState, useEffect, useMemo } from 'react';
import { CheckCircleIcon } from '@heroicons/react/24/solid';
import Uppy from '@uppy/core';
import { UppyContextProvider } from '@uppy/react';
import Dashboard from '@uppy/react/dashboard';
import Tus from '@uppy/tus';

import { useInterval } from '../../../hooks';
import { ErrorResponseBody, ValidationError } from '../../../../types/uppy';
import { refreshTokenIfNeeded } from '../../../../api';

interface IndoorProjectUploadInlineProps {
  indoorProjectId: string;
  fileType: '.xlsx' | '.tar';
  activeTreatment?: string | null;
  onUploadSuccess?: () => void;
  onUploadStateChange?: (isUploading: boolean) => void;
}

function initUppyWithTus(indoorProjectId: string, treatment?: string | null) {
  const headers: Record<string, string> = {
    'X-Indoor-Project-ID': indoorProjectId,
  };

  if (treatment) {
    headers['X-Treatment'] = treatment;
  }

  return new Uppy({
    // Customize file IDs before files are added to include project and treatment context
    // Since @uppy/tus uses file.id in its fingerprint, this ensures
    // the same file uploaded to different projects/treatments is treated as separate uploads
    onBeforeFileAdded: (currentFile) => {
      const modifiedFile = {
        ...currentFile,
        id: [currentFile.id, indoorProjectId, treatment || 'no-treatment'].join(
          '__'
        ),
      };

      return modifiedFile;
    },
  }).use(Tus, {
    endpoint: '/files',
    headers,
  });
}

export default function IndoorProjectUploadInline({
  indoorProjectId,
  fileType = '.xlsx',
  activeTreatment = null,
  onUploadSuccess,
  onUploadStateChange,
}: IndoorProjectUploadInlineProps) {
  const [uppy] = useState(() =>
    initUppyWithTus(indoorProjectId, activeTreatment)
  );
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [pollStartTime, setPollStartTime] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Polling function to check for uploaded data
  const checkForUploadedData = () => {
    if (!uploadSuccess || !onUploadSuccess || !pollStartTime) return;

    // Stop polling after 60 seconds
    const elapsed = Date.now() - pollStartTime;
    const seconds = Math.round(elapsed / 1000);
    setElapsedSeconds(seconds);

    if (elapsed > 60000) {
      setIsPolling(false);
      return;
    }

    setIsPolling(false);
    onUploadSuccess();
    return;
  };

  // Use polling when upload is successful
  useInterval(checkForUploadedData, isPolling ? 2000 : null); // Poll every 2 seconds

  useEffect(() => {
    if (uploadSuccess && onUploadSuccess && !isPolling) {
      setIsPolling(true);
      setPollStartTime(Date.now());
      setElapsedSeconds(0);
    }
  }, [uploadSuccess, onUploadSuccess, isPolling]);

  const restrictions = useMemo(
    () => ({
      allowedFileTypes:
        fileType === '.xlsx'
          ? [
              'application/vnd.ms-excel',
              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            ]
          : ['application/x-tar'],
      maxNumberOfFiles: 1,
      minNumberOfFiles: 1,
    }),
    [fileType]
  );

  useEffect(() => {
    // Set restrictions
    uppy.setOptions({ restrictions });

    const handleRestrictionFailed = () => {
      uppy.info(
        {
          message: 'Unsupported file type',
          details: `Upload must be one of the following file types: ${restrictions.allowedFileTypes.join(
            ', '
          )}`,
        },
        'error',
        5000
      );
    };

    const handleUpload = async () => {
      // Mark upload as started
      if (onUploadStateChange) {
        onUploadStateChange(true);
      }

      // Refresh token if needed before upload starts
      const tokenRefreshed = await refreshTokenIfNeeded();
      if (!tokenRefreshed) {
        // Token refresh failed, cancel upload
        uppy.cancelAll();
        uppy.info(
          {
            message: 'Authentication required',
            details: 'Please log in again to continue uploading.',
          },
          'error',
          5000
        );
        if (onUploadStateChange) {
          onUploadStateChange(false);
        }
        return;
      }
    };

    const handleUploadError = async (
      _file: { id: string } | undefined,
      _error: unknown,
      response?: { status?: number; body?: unknown }
    ) => {
      // Mark upload as finished on error
      if (onUploadStateChange) {
        onUploadStateChange(false);
      }

      // Handle auth expiry propagated as 500 from tusd hook endpoint
      if (
        response &&
        response.status === 500 &&
        response.body &&
        (response.body as ErrorResponseBody).detail
      ) {
        const bodyDetail = (response.body as ErrorResponseBody).detail;
        const detail = typeof bodyDetail === 'string' ? bodyDetail : '';
        if (
          typeof detail === 'string' &&
          detail.includes('Access token expired')
        ) {
          uppy.info(
            {
              message: 'Session expired',
              details: 'Refreshing authentication and retrying upload...',
            },
            'info',
            3000
          );

          const tokenRefreshed = await refreshTokenIfNeeded();
          if (tokenRefreshed && _file) {
            // Mark as uploading again since we're retrying
            if (onUploadStateChange) {
              onUploadStateChange(true);
            }
            setTimeout(() => {
              uppy.retryUpload(_file.id);
            }, 1000);
            return;
          } else {
            uppy.info(
              {
                message: 'Authentication failed',
                details: 'Please log in again to continue uploading.',
              },
              'error',
              5000
            );
            return;
          }
        }
      }
      if (response?.body) {
        let errorDetails = '';
        const body = response.body as ErrorResponseBody;

        if (body.detail) {
          if (typeof body.detail === 'string') {
            errorDetails = body.detail;
          } else if (response.status === 422 && Array.isArray(body.detail)) {
            const validationErrors = body.detail as ValidationError[];
            validationErrors.forEach((err, idx) => {
              errorDetails = `${err.loc[1]}: ${err.msg}`;
              errorDetails += idx < validationErrors.length - 1 ? '; ' : '';
            });
          } else {
            errorDetails = 'Unexpected error occurred';
          }
        } else {
          errorDetails = 'Upload failed';
        }

        uppy.info(
          {
            message: `Error ${response.status}`,
            details: errorDetails,
          },
          'error',
          10000
        );
      }
    };

    const handleComplete = (result: { successful?: unknown[] }) => {
      // Mark upload as finished
      if (onUploadStateChange) {
        onUploadStateChange(false);
      }

      if (result.successful && result.successful.length > 0) {
        setUploadSuccess(true);
      }
    };

    const handleCancelAll = () => {
      // Mark upload as finished if user cancels
      if (onUploadStateChange) {
        onUploadStateChange(false);
      }
    };

    // Register event listeners
    uppy.on('restriction-failed', handleRestrictionFailed);
    uppy.on('upload', handleUpload);
    uppy.on('upload-error', handleUploadError);
    uppy.on('complete', handleComplete);
    uppy.on('cancel-all', handleCancelAll);

    // Cleanup function to remove listeners
    return () => {
      uppy.off('restriction-failed', handleRestrictionFailed);
      uppy.off('upload', handleUpload);
      uppy.off('upload-error', handleUploadError);
      uppy.off('complete', handleComplete);
      uppy.off('cancel-all', handleCancelAll);
    };
  }, [
    uppy,
    restrictions,
    onUploadStateChange,
    fileType,
    indoorProjectId,
    activeTreatment,
  ]);

  if (uploadSuccess) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-white rounded-lg">
        <CheckCircleIcon className="w-12 h-12 text-green-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Upload Successful!
        </h3>
        <p className="text-gray-600 text-center">
          Your file has been received and is being processed.
          {isPolling && (
            <span className="block mt-2 text-sm text-gray-500">
              Checking for processed data... ({elapsedSeconds}s)
            </span>
          )}
          {!isPolling && uploadSuccess && (
            <span className="block mt-2 text-sm text-green-600">
              Data found! Refreshing page...
            </span>
          )}
        </p>
      </div>
    );
  }

  return (
    <UppyContextProvider uppy={uppy}>
      <div className="relative flex flex-col gap-3">
        <div className="inline-block">
          <Dashboard uppy={uppy} height={200} width="auto" />
        </div>
      </div>
    </UppyContextProvider>
  );
}
