import '@uppy/core/css/style.min.css';
import '@uppy/dashboard/css/style.min.css';

import { useEffect, useMemo, useState } from 'react';
import Uppy from '@uppy/core';
import Dashboard from '@uppy/react/dashboard';
import Tus from '@uppy/tus';

import { refreshTokenIfNeeded } from '../../../api';

interface AnnotationAttachmentUploadProps {
  projectId: string;
  flightId: string;
  dataProductId: string;
  annotationId: string;
  onUploadComplete: () => void;
}

function createUppy(props: {
  projectId: string;
  flightId: string;
  dataProductId: string;
  annotationId: string;
}) {
  return new Uppy().use(Tus, {
    endpoint: '/files',
    headers: {
      'X-Project-ID': props.projectId,
      'X-Flight-ID': props.flightId,
      'X-Data-Type': 'annotation_attachment',
      'X-Annotation-ID': props.annotationId,
      'X-Data-Product-ID': props.dataProductId,
    },
    removeFingerprintOnSuccess: true,
  });
}

export default function AnnotationAttachmentUpload({
  projectId,
  flightId,
  dataProductId,
  annotationId,
  onUploadComplete,
}: AnnotationAttachmentUploadProps) {
  const uppyConfig = useMemo(
    () => ({ projectId, flightId, dataProductId, annotationId }),
    [projectId, flightId, dataProductId, annotationId]
  );
  const [uppy, setUppy] = useState(() => createUppy(uppyConfig));

  useEffect(() => {
    setUppy(() => createUppy(uppyConfig));
  }, [uppyConfig]);

  const restrictions = useMemo(
    () => ({
      allowedFileTypes: [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'video/mp4',
        'video/quicktime',
        'video/webm',
        'video/x-msvideo',
      ],
      maxNumberOfFiles: 10,
      minNumberOfFiles: 1,
    }),
    []
  );

  useEffect(() => {
    uppy.setOptions({ restrictions });

    const handleRestrictionFailed = () => {
      uppy.info(
        {
          message: 'Unsupported file type',
          details:
            'Only image (JPG, PNG, GIF, WebP) and video (MP4, MOV, WebM, AVI) files are allowed.',
        },
        'error',
        5000
      );
    };

    const handleUpload = async () => {
      const tokenRefreshed = await refreshTokenIfNeeded();
      if (!tokenRefreshed) {
        uppy.cancelAll();
        uppy.info(
          {
            message: 'Authentication required',
            details: 'Please log in again to continue uploading.',
          },
          'error',
          5000
        );
      }
    };

    const handleUploadSuccess = () => {
      onUploadComplete();
    };

    const handleUploadError = (
      _file: { id: string } | undefined,
      _error: unknown,
      response?: { status?: number; body?: unknown }
    ) => {
      if (response?.body) {
        const body = response.body as { detail?: string };
        uppy.info(
          {
            message: `Error ${response.status}`,
            details: body.detail || 'Upload failed',
          },
          'error',
          10000
        );
      }
    };

    uppy.on('restriction-failed', handleRestrictionFailed);
    uppy.on('upload', handleUpload);
    uppy.on('upload-success', handleUploadSuccess);
    uppy.on('upload-error', handleUploadError);

    return () => {
      uppy.off('restriction-failed', handleRestrictionFailed);
      uppy.off('upload', handleUpload);
      uppy.off('upload-success', handleUploadSuccess);
      uppy.off('upload-error', handleUploadError);
    };
  }, [uppy, restrictions, onUploadComplete]);

  return (
    <Dashboard
      uppy={uppy}
      height="200px"
      locale={{
        strings: {
          dropPasteFiles: 'Drop images or videos here or %{browseFiles}',
        },
      }}
      proudlyDisplayPoweredByUppy={false}
    />
  );
}
