import '@uppy/core/css/style.min.css';
import '@uppy/dashboard/css/style.min.css';

import { useState, Dispatch, SetStateAction, useEffect, useMemo } from 'react';
import { CheckCircleIcon } from '@heroicons/react/24/solid';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/dashboard';
import Tus from '@uppy/tus';

import { IndoorProjectUploadInputProps } from './IndoorProject';
import Modal from '../../../Modal';
import { useInterval } from '../../../hooks';
import {
  ErrorResponseBody,
  ValidationError,
} from '../../../../types/uppy';
import { refreshTokenIfNeeded } from '../../../../api';

type IndoorProjectUploadModalProps = {
  btnLabel?: string;
  indoorProjectId: string;
  isOpen?: boolean;
  setIsOpen?: Dispatch<SetStateAction<boolean>>;
  hideBtn?: boolean;
  fileType?: string;
  activeTreatment?: string | null;
  onUploadSuccess?: () => void;
};

export default function IndoorProjectUploadModal({
  btnLabel = 'Upload',
  indoorProjectId,
  isOpen: controlledIsOpen,
  setIsOpen: controlledSetIsOpen,
  hideBtn = false,
  fileType = '.xlsx',
  activeTreatment = null,
  onUploadSuccess,
}: IndoorProjectUploadModalProps) {
  const [internalIsOpen, setInternalIsOpen] = useState<boolean>(false);

  // Use controlled state if provided, otherwise use internal state
  const isOpen = controlledIsOpen ?? internalIsOpen;
  const setIsOpen = controlledSetIsOpen ?? setInternalIsOpen;

  const handleUploadSuccess = () => {
    if (onUploadSuccess) {
      onUploadSuccess();
    }
    // Close the modal after triggering refetch
    setIsOpen(false);
  };

  const handleClick = () => setIsOpen(!isOpen);

  return (
    <div className="relative">
      {!controlledIsOpen && !hideBtn && (
        <div className="flex">
          <button
            type="button"
            onClick={handleClick}
            className="w-full px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
          >
            {btnLabel}
          </button>
        </div>
      )}
      <Modal open={isOpen} setOpen={setIsOpen}>
        <div className="relative flex flex-col p-4 gap-2 bg-[#FAFAFA]">
          <span className="block font-bold">Required files:</span>
          <ul className="list-disc list-inside">
            {fileType === '.xlsx' ? (
              <li>Spreadsheet (.xls, .xlsx)</li>
            ) : (
              <li>TAR archive (.tar)</li>
            )}
          </ul>
          <IndoorProjectUploadInput
            indoorProjectId={indoorProjectId}
            fileType={fileType}
            activeTreatment={activeTreatment}
            onUploadSuccess={handleUploadSuccess}
          />
        </div>
      </Modal>
    </div>
  );
}

function initUppyWithTus(indoorProjectId, treatment?: string | null) {
  const headers = {
    'X-Indoor-Project-ID': indoorProjectId,
  };

  if (treatment) {
    headers['X-Treatment'] = treatment;
  }

  return new Uppy().use(Tus, {
    endpoint: '/files',
    headers,
  });
}

function IndoorProjectUploadInput({
  indoorProjectId,
  fileType = '.xlsx',
  activeTreatment = null,
  onUploadSuccess,
}: IndoorProjectUploadInputProps & {
  fileType?: string;
  onUploadSuccess?: () => void;
}) {
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
      console.log('Polling timeout reached (60s), stopping...');
      setIsPolling(false);
      return;
    }

    console.log(`Polling for uploaded data... (${seconds}s elapsed)`);

    setIsPolling(false);
    onUploadSuccess();
    return;
  };

  // Use polling when upload is successful
  useInterval(checkForUploadedData, isPolling ? 2000 : null); // Poll every 2 seconds

  useEffect(() => {
    if (uploadSuccess && onUploadSuccess && !isPolling) {
      console.log('Upload successful, starting to poll for data...');
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

    const handleRestrictionFailed = (e: unknown) => {
      console.log(e);
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
        return;
      }
    };

    const handleUploadError = async (
      _file: { id: string } | undefined,
      _error: unknown,
      response?: { status?: number; body?: unknown }
    ) => {
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
      if (result.successful && result.successful.length > 0) {
        setUploadSuccess(true);
      }
    };

    // Register event listeners
    uppy.on('restriction-failed', handleRestrictionFailed);
    uppy.on('upload', handleUpload);
    uppy.on('upload-error', handleUploadError);
    uppy.on('complete', handleComplete);

    // Cleanup function to remove listeners
    return () => {
      uppy.off('restriction-failed', handleRestrictionFailed);
      uppy.off('upload', handleUpload);
      uppy.off('upload-error', handleUploadError);
      uppy.off('complete', handleComplete);
    };
  }, [uppy, restrictions]);

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
    <div className="relative flex flex-col gap-2">
      <Dashboard
        uppy={uppy}
        height={400}
        locale={{
          strings: {
            dropHint: 'Drop here or %{myDevice}',
            myDevice: 'browse local files',
          },
        }}
        proudlyDisplayPoweredByUppy={false}
      />
    </div>
  );
}
