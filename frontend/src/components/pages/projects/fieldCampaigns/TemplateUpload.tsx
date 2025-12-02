import { useEffect, useState } from 'react';
import Uppy from '@uppy/core';
import DashboardModal from '@uppy/react/lib/DashboardModal';
import XHRUpload from '@uppy/xhr-upload';

// Don't forget the CSS: core and the UI components + plugins you are using.
import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

// Don’t forget to keep the Uppy instance outside of your component.
function createUppy(endpoint: string) {
  return new Uppy().use(XHRUpload, {
    endpoint: endpoint,
    method: 'post',
    formData: true,
    fieldName: 'files',
  });
}

interface TemplateUpload {
  endpoint: string;
  open: boolean;
  onSuccess: () => void;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function TemplateUpload({
  endpoint,
  open = false,
  onSuccess,
  setOpen,
}: TemplateUpload) {
  const [uppy] = useState(() => createUppy(endpoint));

  const restrictions = {
    allowedFileTypes: ['.csv'],
    maxNumberOfFiles: 1,
    minNumberOfFiles: 1,
  };

  useEffect(() => {
    if (endpoint) {
      uppy.setOptions({
        restrictions,
      });
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

  uppy.on('upload', (_uploadID, files) => {
    if (files && files.length > 0) {
      const file = files[0];
      uppy.setFileState(file.id, {
        xhrUpload: {
          // @ts-ignore
          ...file.xhrUpload,
          endpoint: endpoint,
        },
      });
    }
  });

  uppy.on('upload-error', (_file, _error, response) => {
    if (response?.body) {
      let errorDetails = '';
      const body = response.body as Record<string, any>;

      if (body.detail) {
        if (typeof body.detail === 'string') {
          errorDetails = body.detail;
        } else if (response.status === 422 && Array.isArray(body.detail)) {
          body.detail.forEach((err: any, idx: number) => {
            errorDetails = `${err.loc[1]}: ${err.msg}`;
            errorDetails += idx < body.detail.length - 1 ? '; ' : '';
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
      disableThumbnailGenerator={true}
      locale={{
        strings: { dropPasteFiles: 'Drop csv template here or %{browseFiles}' },
      }}
    />
  );
}
