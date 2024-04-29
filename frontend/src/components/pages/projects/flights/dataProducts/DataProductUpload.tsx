import { useEffect, useState } from 'react';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/lib/Dashboard';
import Tus from '@uppy/tus';

import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

type DataProductInfo = {
  dtype: string;
  endpoint: string;
  flightID: string;
  projectID: string;
};

function createUppy(info: DataProductInfo) {
  return new Uppy().use(Tus, {
    endpoint: info.endpoint,
    headers: {
      'X-Project-ID': info.projectID,
      'X-Flight-ID': info.flightID,
      'X-Data-Type': info.dtype,
    },
    removeFingerprintOnSuccess: true,
  });
}

type DataProductUpload = {
  info: DataProductInfo;
  fileType: string[];
  uploadType: string;
  updateSetDisabled: (param: boolean) => void;
  updateUploadHistory?: (param: string) => void;
};

export default function DataProductUpload({
  info,
  fileType,
  uploadType,
  updateSetDisabled,
  updateUploadHistory,
}: DataProductUpload) {
  const [uppy, updateUppy] = useState(() => createUppy(info));

  useEffect(() => {
    // updates custom headers when data type, project id, or flight id change
    updateUppy(() => createUppy(info));
  }, [info.dtype]);

  const restrictions = {
    allowedFileTypes: fileType,
    maxNumberOfFiles: 1,
    minNumberOfFiles: 1,
  };

  uppy.setOptions({ restrictions });

  uppy.on('restriction-failed', () => {
    uppy.info(
      {
        message: 'Unsupported file extension',
        details: `Upload must be one of the following file types: ${restrictions.allowedFileTypes.join(
          ', '
        )}`,
      },
      'error',
      5000
    );
  });

  uppy.on('upload', () => {
    // disable data type inputs during upload
    updateSetDisabled(true);
  });

  uppy.on('upload-error', (_file, _error, response) => {
    // re-enable data type inputs
    updateSetDisabled(false);
    if (response && response.body && response.body.detail) {
      let errorDetails = '';
      if (typeof response.body.detail === 'string') {
        errorDetails = response.body.detail;
      } else if (response.status === 422 && Array.isArray(response.body.detail)) {
        response.body.detail.forEach((err, idx) => {
          errorDetails = `${err.loc[1]}: ${err.msg}`;
          errorDetails += idx < response.body.detail.length - 1 ? '; ' : '';
        });
      } else {
        errorDetails = 'Unexpected error occurred';
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
  });

  uppy.on('upload-success', (_file, _response) => {
    // re-enable data type inputs
    updateSetDisabled(false);
    if (_file && updateUploadHistory) updateUploadHistory(_file.meta.name);
    if (_file) uppy.removeFile(_file.id);
  });

  return (
    <Dashboard
      uppy={uppy}
      height="240px"
      locale={{
        strings: { dropPasteFiles: 'Drop data product here or %{browseFiles}' },
      }}
      proudlyDisplayPoweredByUppy={false}
      disableThumbnailGenerator={uploadType !== 'img'}
    />
  );
}
