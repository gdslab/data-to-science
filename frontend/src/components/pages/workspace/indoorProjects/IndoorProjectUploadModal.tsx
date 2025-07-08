import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

import { useState, Dispatch, SetStateAction, useEffect } from 'react';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/lib/Dashboard';
import Tus from '@uppy/tus';
import { CheckCircleIcon } from '@heroicons/react/24/solid';

import { IndoorProjectUploadInputProps } from './IndoorProject';
import Modal from '../../../Modal';
import { useInterval } from '../../../hooks';
import { useIndoorProjectData } from './hooks/useIndoorProjectData';

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
  console.log('treatment', treatment);
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
  console.log('activeTreatment', activeTreatment);
  const [uppy, _setUppy] = useState(() =>
    initUppyWithTus(indoorProjectId, activeTreatment)
  );
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [pollStartTime, setPollStartTime] = useState<number | null>(null);

  // Polling function to check for uploaded data
  const checkForUploadedData = () => {
    console.log('checking for uploaded data');
    if (!uploadSuccess || !onUploadSuccess || !pollStartTime) return;

    console.log('uploadSuccess', uploadSuccess);
    console.log('onUploadSuccess', onUploadSuccess);
    console.log('pollStartTime', pollStartTime);

    // Stop polling after 60 seconds
    const elapsed = Date.now() - pollStartTime;
    if (elapsed > 60000) {
      console.log('Polling timeout reached (60s), stopping...');
      setIsPolling(false);
      return;
    }

    console.log(
      `Polling for uploaded data... (${Math.round(elapsed / 1000)}s elapsed)`
    );

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
    }
  }, [uploadSuccess, onUploadSuccess, isPolling]);

  const restrictions = {
    allowedFileTypes:
      fileType === '.xlsx'
        ? [
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          ]
        : ['application/x-tar'],
    maxNumberOfFiles: 1,
    minNumberOfFiles: 1,
  };

  uppy.setOptions({ restrictions });

  uppy.on('restriction-failed', (e) => {
    console.log(e);
  });

  uppy.on('complete', (result) => {
    if (result.successful.length > 0) {
      setUploadSuccess(true);
    }
  });

  if (uploadSuccess) {
    const elapsed = pollStartTime
      ? Math.round((Date.now() - pollStartTime) / 1000)
      : 0;

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
              Checking for processed data... ({elapsed}s)
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
            dropHereOr: 'Drop here or %{browse}',
            browse: 'browse local files',
          },
        }}
        proudlyDisplayPoweredByUppy={false}
      />
    </div>
  );
}
