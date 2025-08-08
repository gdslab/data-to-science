import { FeatureCollection } from 'geojson';
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

interface ShapefileUpload {
  endpoint: string;
  open: boolean;
  onSuccess: () => void;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setUploadResponse: React.Dispatch<
    React.SetStateAction<FeatureCollection | null>
  >;
}

export default function ShapefileUpload({
  endpoint,
  open = false,
  onSuccess,
  setOpen,
  setUploadResponse,
}: ShapefileUpload) {
  const [uppy] = useState(() => createUppy(endpoint));

  const restrictions = {
    allowedFileTypes: ['.geojson', '.json', '.zip'],
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
      } else if (
        response.status === 422 &&
        Array.isArray(response.body.detail)
      ) {
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
    if (response && response.status === 200 && setUploadResponse) {
      setUploadResponse(response.body);
    }
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
        strings: {
          dropPasteFiles: 'Drop GeoJSON or zip file here or %{browseFiles}',
        },
      }}
    />
  );
}
