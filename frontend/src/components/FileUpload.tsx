import { useEffect, useState } from 'react';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/lib/Dashboard';
import XHRUpload from '@uppy/xhr-upload';

// Don't forget the CSS: core and the UI components + plugins you are using.
import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

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
  uploadType: string;
}

function checkForMissingShpParts(files) {
  const requiredParts = [
    { ext: 'shp', included: false },
    { ext: 'shx', included: false },
    { ext: 'dbf', included: false },
  ];
  const updateRequiredParts = (part) =>
    (requiredParts.filter(({ ext }) => ext === part)[0]['included'] = true);
  files.forEach(({ extension }) =>
    extension === 'shp'
      ? updateRequiredParts('shp')
      : extension === 'shx'
      ? updateRequiredParts('shx')
      : extension === 'dbf'
      ? updateRequiredParts('dbf')
      : null
  );
  return requiredParts.filter(({ included }) => included === false);
}

function containsZip(files) {
  const zipFile = files.filter(({ extension }) => extension === 'zip');
  if (zipFile.length === 1) return true;
  return false;
}

export default function FileUpload({ endpoint, restrictions, uploadType }: FileUpload) {
  const [uppy] = useState(() => createUppy(endpoint));

  useEffect(() => {
    if (endpoint) {
      uppy.setOptions({ restrictions });
      uppy.setOptions({
        onBeforeUpload: (files) => {
          console.log(files);
          if (uploadType === 'shp') {
            return true;
          }
          if (uploadType === 'tif') {
            console.log(files);
            return true;
          }
          return false;
        },
      });
    }
  }, [uppy, endpoint]);

  uppy.on('files-added', (files) => {
    console.log(files);
    if (files.length > 1 && containsZip(files)) {
      files.forEach(({ id }) => uppy.removeFile(id));
      uppy.info({
        message: 'Too many files',
        details:
          'Upload a single .zip or individual shapefile parts (.shp, .shx, .dbf)',
      });
      return;
    }
    if (files.length === 1 && containsZip(files)) return;
    if (files.length > 0 && !containsZip(files)) {
      const missingParts = checkForMissingShpParts(files);
      if (missingParts.length > 0) {
        uppy.info(
          {
            message: `Missing required shapefile part${
              missingParts.length > 1 ? 's' : ''
            }`,
            details: `Missing ${missingParts.map((part) => part.ext).join(', ')}`,
          },
          'warning',
          5000
        );
      }
    }
  });

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

  return <Dashboard uppy={uppy} height="240px" />;
}
