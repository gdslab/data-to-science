import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

import { useEffect, useState } from 'react';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/lib/Dashboard';
import Tus from '@uppy/tus';

import { refreshTokenIfNeeded } from '../../../../../api';
import { ErrorResponseBody, ValidationError } from '../../../../../types/uppy';

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
  }, [info]);

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

  uppy.on('upload', async () => {
    // disable data type inputs during upload
    updateSetDisabled(true);

    // Refresh token if needed before upload starts
    const tokenRefreshed = await refreshTokenIfNeeded();
    if (!tokenRefreshed) {
      // Token refresh failed, cancel upload
      uppy.cancelAll();
      updateSetDisabled(false);
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
  });

  uppy.on('upload-error', async (_file, _error, response) => {
    // re-enable data type inputs
    updateSetDisabled(false);

    // Handle auth expiry propagated as 500 from tusd hook endpoint
    if (
      response &&
      response.status === 500 &&
      response.body &&
      response.body.detail
    ) {
      const detail =
        typeof response.body.detail === 'string' ? response.body.detail : '';
      if (detail.includes('Access token expired')) {
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
        strings: {
          dropPasteFiles:
            uploadType === 'rawData'
              ? 'Drop zipped raw data here or %{browseFiles}'
              : 'Drop data product here or %{browseFiles}',
        },
      }}
      proudlyDisplayPoweredByUppy={false}
      disableThumbnailGenerator={uploadType !== 'img'}
      showProgressDetails={true}
    />
  );
}
