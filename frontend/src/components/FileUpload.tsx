import { useEffect, useState } from 'react';
import Uppy from '@uppy/core';
import DragDrop from '@uppy/react/lib/DragDrop';
import StatusBar from '@uppy/react/lib/StatusBar';
import XHRUpload from '@uppy/xhr-upload';

// Don't forget the CSS: core and the UI components + plugins you are using.
import '@uppy/core/dist/style.min.css';
import '@uppy/drag-drop/dist/style.min.css';
import '@uppy/status-bar/dist/style.min.css';

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
  maxNumberOfFiles: number;
}

interface FileUpload {
  restrictions: Restrictions;
  endpoint: string;
}

export default function FileUpload({ restrictions, endpoint }: FileUpload) {
  const [uppy] = useState(() => createUppy(endpoint));

  useEffect(() => {
    if (endpoint) {
      uppy.setOptions({ restrictions });
    }
  }, [uppy, endpoint]);

  uppy.on('restriction-failed', (file, error) => {
    uppy.info(
      {
        message: 'Unsupported file extension',
        details: `Upload must be one of the following file types: ${restrictions.allowedFileTypes.join(
          ', '
        )}`,
      },
      'error',
      10000
    );
  });

  return (
    <div className="mt-4">
      <DragDrop uppy={uppy} height="175px" />
      <StatusBar uppy={uppy} />
    </div>
  );
}
