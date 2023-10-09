import { useEffect, useState } from 'react';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/lib/Dashboard';
import DashboardModal from '@uppy/react/lib/DashboardModal';
import XHRUpload from '@uppy/xhr-upload';

// Don't forget the CSS: core and the UI components + plugins you are using.
import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

import { FeatureCollection } from './maps/MapModal';

// Don’t forget to keep the Uppy instance outside of your component.
function createUppy(upload_endpoint: string) {
  return new Uppy().use(XHRUpload, {
    endpoint: upload_endpoint,
    method: 'post',
    formData: true,
    fieldName: 'files',
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
          ...file.xhrUpload,
          endpoint: endpoint,
        },
      });
    }
  });

  uppy.on('upload-success', (_file, response) => {
    if (response.status === 200 && uploadType === 'shp' && setUploadResponse) {
      setUploadResponse(response.body);
    }
    if (onSuccess) onSuccess();
  });

  if (inline) {
    return <Dashboard uppy={uppy} height="240px" />;
  } else {
    return (
      <DashboardModal uppy={uppy} open={open} onRequestClose={() => setOpen(false)} />
    );
  }
}
