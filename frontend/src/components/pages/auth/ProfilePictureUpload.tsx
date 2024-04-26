import { useEffect, useState } from 'react';
import Uppy from '@uppy/core';
import DashboardModal from '@uppy/react/lib/DashboardModal';
import XHRUpload from '@uppy/xhr-upload';

import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

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

  const restrictions = {
    allowedFileTypes: ['.jpg', '.png'],
    maxNumberOfFiles: 1,
    minNumberOfFiles: 1,
  };

  useEffect(() => {
    if (endpoint) {
      uppy.setOptions({ restrictions });
    }
  }, [uppy, endpoint]);

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

  uppy.on('upload', (data) => {
    if (data && data.fileIDs && data.fileIDs.length > 0) {
      const file = uppy.getFile(data.fileIDs[0]);
      uppy.setFileState(data.fileIDs[0], {
        xhrUpload: {
          // @ts-ignore
          ...file.xhrUpload,
          endpoint: endpoint,
        },
      });
    }
  });

  uppy.on('upload-error', (_file, _error, response) => {
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
    if (_file) uppy.removeFile(_file.id);
    if (onSuccess) onSuccess();
  });

  return (
    <DashboardModal
      uppy={uppy}
      open={open}
      onRequestClose={() => setOpen(false)}
      closeAfterFinish={true}
      proudlyDisplayPoweredByUppy={false}
      locale={{
        strings: { dropPasteFiles: 'Drop profile picture here or %{browseFiles}' },
      }}
    />
  );
}
