import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

import { useState, Dispatch, SetStateAction, useEffect } from 'react';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/lib/Dashboard';
import Tus from '@uppy/tus';
import { CheckCircleIcon } from '@heroicons/react/24/solid';

import { IndoorProjectUploadInputProps } from './IndoorProject';
import Modal from '../../../Modal';
import { useIndoorProjectData } from './hooks/useIndoorProjectData';

type IndoorProjectUploadModalProps = {
  btnLabel?: string;
  indoorProjectId: string;
  isOpen?: boolean;
  setIsOpen?: Dispatch<SetStateAction<boolean>>;
  hideBtn?: boolean;
  fileType?: string;
  activeTreatment?: string | null;
};

export default function IndoorProjectUploadModal({
  btnLabel = 'Upload',
  indoorProjectId,
  isOpen: controlledIsOpen,
  setIsOpen: controlledSetIsOpen,
  hideBtn = false,
  fileType = '.xlsx',
  activeTreatment = null,
}: IndoorProjectUploadModalProps) {
  const [internalIsOpen, setInternalIsOpen] = useState<boolean>(false);

  // Use controlled state if provided, otherwise use internal state
  const isOpen = controlledIsOpen ?? internalIsOpen;
  const setIsOpen = controlledSetIsOpen ?? setInternalIsOpen;

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
          />
        </div>
      </Modal>
    </div>
  );
}

function initUppyWithTus(indoorProjectId) {
  return new Uppy().use(Tus, {
    endpoint: '/files',
    headers: {
      'X-Indoor-Project-ID': indoorProjectId,
    },
  });
}

function IndoorProjectUploadInput({
  indoorProjectId,
  fileType = '.xlsx',
  activeTreatment = null,
}: IndoorProjectUploadInputProps & { fileType?: string }) {
  const [uppy, _setUppy] = useState(() => initUppyWithTus(indoorProjectId));
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const { indoorProjectData, isLoadingData } = useIndoorProjectData({
    indoorProjectId,
  });

  useEffect(() => {
    if (!uploadSuccess || isLoadingData) return;

    if (fileType === '.xlsx') {
      // For spreadsheet uploads, check if we have any spreadsheet data
      const hasSpreadsheet = indoorProjectData.some(
        (data) => data.file_type === '.xlsx'
      );
      if (hasSpreadsheet) {
        window.location.reload();
      }
    } else if (fileType === '.tar' && activeTreatment) {
      // For TAR uploads, check if we have the specific treatment data
      const hasTar = indoorProjectData.some(
        (data) =>
          data.file_type === '.tar' &&
          data.directory_structure?.name === activeTreatment
      );
      if (hasTar) {
        window.location.reload();
      }
    }
  }, [
    uploadSuccess,
    isLoadingData,
    indoorProjectData,
    fileType,
    activeTreatment,
  ]);

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
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-white rounded-lg">
        <CheckCircleIcon className="w-12 h-12 text-green-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Upload Successful!
        </h3>
        <p className="text-gray-600 text-center">
          Your file has been received and is being processed. This may take a
          few moments.
          {isLoadingData && (
            <span className="block mt-2 text-sm text-gray-500">
              Checking for updates...
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
