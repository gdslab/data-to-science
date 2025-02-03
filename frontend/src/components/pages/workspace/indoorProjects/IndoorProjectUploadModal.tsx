import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

import { useState } from 'react';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/lib/Dashboard';
import Tus from '@uppy/tus';

import { Button } from '../../../Buttons';
import { IndoorProjectUploadInputProps } from './IndoorProject';
import Modal from '../../../Modal';

type IndoorProjectUploadModalProps = {
  btnLabel?: string;
  indoorProjectId: string;
};

export default function IndoorProjectUploadModal({
  btnLabel = 'Upload',
  indoorProjectId,
}: IndoorProjectUploadModalProps) {
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const handleClick = () => setIsOpen(!isOpen);
  return (
    <div className="relative">
      <div className="flex">
        <button
          type="button"
          onClick={handleClick}
          className="w-full px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
        >
          {btnLabel}
        </button>
      </div>
      <Modal open={isOpen} setOpen={setIsOpen}>
        <div className="relative flex flex-col p-4 gap-2 bg-[#FAFAFA]">
          <span className="block font-bold">Required files:</span>
          <ul className="list-disc list-inside">
            <li>Spreadsheet (.xls, .xlsx)</li>
            <li>TAR archive (.tar)</li>
          </ul>
          <IndoorProjectUploadInput indoorProjectId={indoorProjectId} />
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

function IndoorProjectUploadInput({ indoorProjectId }: IndoorProjectUploadInputProps) {
  const [uppy, _setUppy] = useState(() => initUppyWithTus(indoorProjectId));

  const restrictions = {
    allowedFileTypes: [
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/x-tar',
    ],
    maxNumberOfFiles: 2,
    minNumberOfFiles: 1,
  };

  uppy.setOptions({ restrictions });

  uppy.on('restriction-failed', (e) => {
    console.log(e);
  });

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
