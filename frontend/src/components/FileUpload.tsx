import { useEffect, useState } from 'react';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/lib/Dashboard';
import DashboardModal from '@uppy/react/lib/DashboardModal';
// import XHRUpload from '@uppy/xhr-upload';
import Tus from '@uppy/tus';

// Don't forget the CSS: core and the UI components + plugins you are using.
import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

import { FeatureCollection } from './pages/projects/Project';

// Don’t forget to keep the Uppy instance outside of your component.
function createUppy(upload_endpoint: string) {
  console.log('upload_endpoint', upload_endpoint);
  // return new Uppy().use(XHRUpload, {
  //   endpoint: upload_endpoint,
  //   method: 'post',
  //   formData: true,
  //   fieldName: 'files',
  // });
  return new Uppy().use(Tus, {
    endpoint: `${window.location.origin}/files`,
    async onBeforeRequest(req) {
      console.log(req);
    },
  });
}

interface Restrictions {
  allowedFileTypes: string[];
  minNumberOfFiles: number;
  maxNumberOfFiles: number;
}

interface FileUpload {
  endpoint: string;
  inline?: boolean;
  open?: boolean;
  onSuccess?: () => void;
  setUploadResponse?: React.Dispatch<React.SetStateAction<FeatureCollection | null>>;
  restrictions: Restrictions;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
  uploadType: string;
  updateUploadHistory?: (param: string) => void;
}

export default function FileUpload({
  endpoint,
  inline = false,
  open = false,
  onSuccess = () => {},
  restrictions,
  setUploadResponse,
  setOpen = () => {},
  uploadType,
  updateUploadHistory,
}: FileUpload) {
  const [uppy] = useState(() => createUppy(endpoint));

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

  uppy.on('upload-success', (_file, response) => {
    if (
      response &&
      response.status === 200 &&
      uploadType === 'shp' &&
      setUploadResponse
    ) {
      setUploadResponse(response.body);
    }
    if (_file && updateUploadHistory) updateUploadHistory(_file.meta.name);
    if (_file) uppy.removeFile(_file.id);
    if (onSuccess) onSuccess();
  });

  if (inline) {
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
  } else {
    return (
      <DashboardModal
        uppy={uppy}
        open={open}
        onRequestClose={() => setOpen(false)}
        closeAfterFinish={true}
        proudlyDisplayPoweredByUppy={false}
        disableThumbnailGenerator={uploadType !== 'img'}
        locale={{
          strings: { dropPasteFiles: 'Drop file here or %{browseFiles}' },
        }}
      />
    );
  }
}
