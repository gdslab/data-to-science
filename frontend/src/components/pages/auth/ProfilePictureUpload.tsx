import { useEffect, useMemo, useState } from 'react';
import Uppy from '@uppy/core';
import DashboardModal from '@uppy/react/dashboard-modal';
import XHRUpload from '@uppy/xhr-upload';

import '@uppy/core/css/style.min.css';
import '@uppy/dashboard/css/style.min.css';

import { ErrorResponseBody, ValidationError } from '../../../types/uppy';

function createUppy(upload_endpoint: string) {
  return new Uppy().use(XHRUpload, {
    endpoint: upload_endpoint,
    method: 'post',
    formData: true,
    fieldName: 'files',
  });
}

interface ProfilePictureUpload {
  endpoint: string;
  open?: boolean;
  onSuccess?: () => void;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function ProfilePictureUpload({
  endpoint,
  open = false,
  onSuccess = () => {},
  setOpen = () => {},
}: ProfilePictureUpload) {
  const [uppy] = useState(() => createUppy(endpoint));

  const restrictions = useMemo(
    () => ({
      allowedFileTypes: ['.jpg', '.png'],
      maxNumberOfFiles: 1,
      minNumberOfFiles: 1,
    }),
    []
  );

  useEffect(() => {
    if (endpoint) {
      uppy.setOptions({ restrictions });
    }
  }, [uppy, endpoint, restrictions]);

  useEffect(() => {
    const handleRestrictionFailed = () => {
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
    };

    const handleUpload = (_uploadID: string, files: unknown) => {
      if (files && Array.isArray(files) && files.length > 0) {
        const file = files[0];
        uppy.setFileState(file.id, {
          xhrUpload: {
            ...file.xhrUpload,
            endpoint: endpoint,
          },
        });
      }
    };

    const handleUploadError = (
      _file: unknown,
      _error: unknown,
      response?: { status?: number; body?: unknown }
    ) => {
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

    const handleUploadSuccess = (
      _file: { id: string } | undefined,
      _response: unknown
    ) => {
      if (_file) uppy.removeFile(_file.id);
      if (onSuccess) onSuccess();
    };

    // Register event listeners
    uppy.on('restriction-failed', handleRestrictionFailed);
    uppy.on('upload', handleUpload);
    uppy.on('upload-error', handleUploadError);
    uppy.on('upload-success', handleUploadSuccess);

    // Cleanup function to remove listeners
    return () => {
      uppy.off('restriction-failed', handleRestrictionFailed);
      uppy.off('upload', handleUpload);
      uppy.off('upload-error', handleUploadError);
      uppy.off('upload-success', handleUploadSuccess);
    };
  }, [uppy, endpoint, restrictions, onSuccess]);

  return (
    <DashboardModal
      uppy={uppy}
      open={open}
      onRequestClose={() => setOpen(false)}
      closeAfterFinish={true}
      proudlyDisplayPoweredByUppy={false}
      locale={{
        strings: {
          dropPasteFiles: 'Drop profile picture here or %{browseFiles}',
        },
      }}
    />
  );
}
