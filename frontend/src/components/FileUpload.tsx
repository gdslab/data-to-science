import { useEffect, useState } from 'react';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/lib/Dashboard';
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
  restrictions: Restrictions;
  endpoint: string;
  setUploadResponse: React.Dispatch<React.SetStateAction<FeatureCollection | null>>;
  uploadType: string;
}

export default function FileUpload({
  endpoint,
  restrictions,
  setUploadResponse,
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

  uppy.on('upload-success', (file, response) => {
    if (response.status === 200 && uploadType === 'shp') {
      setUploadResponse(response.body);
    }
  });

  return <Dashboard uppy={uppy} height="240px" />;
}
