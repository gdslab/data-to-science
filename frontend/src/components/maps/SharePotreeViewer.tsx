import { Fragment, useEffect, useMemo } from 'react';
import { useLocation } from 'react-router';

import { AlertBar } from '../Alert';

import api from '../../api';
import { recordDataProductView } from '../../utils/recordDataProductView';

function useQuery() {
  const { search } = useLocation();

  return useMemo(() => new URLSearchParams(search), [search]);
}

export default function SharePotreeViewer() {
  const query = useQuery();
  const fileID = query.get('file_id');

  // Resolve the data product id from the file id, then record a view. The
  // iframe itself only receives the file id, so we look up the product the same
  // way ShareCopcMapViewer does.
  useEffect(() => {
    if (!fileID) return;
    let cancelled = false;
    (async () => {
      try {
        const response = await api.get(`/public?file_id=${fileID}`);
        if (!cancelled && response?.data?.id) {
          recordDataProductView(response.data.id);
        }
      } catch {
        // Best-effort: a failed lookup simply means no view is recorded.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [fileID]);

  // Detect mobile device outside of iframe content
  const isMobile =
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    ) || window.innerWidth < 768;

  // Handle missing file ID
  if (!fileID) {
    return (
      <Fragment>
        <div className="flex items-center justify-center h-full w-full">
          <div className="text-red-600">No file ID provided</div>
        </div>
        <AlertBar alertType="error">No file ID provided</AlertBar>
      </Fragment>
    );
  }

  // Construct the URL to the backend endpoint that serves the Potree viewer
  const shareViewerUrl = `/share-potree-viewer?file_id=${encodeURIComponent(
    fileID
  )}&is_mobile=${isMobile}`;

  return (
    <Fragment>
      <iframe
        className="h-full w-full touch-none"
        src={shareViewerUrl}
        sandbox="allow-same-origin allow-scripts allow-popups allow-pointer-lock allow-modals allow-forms"
      ></iframe>
    </Fragment>
  );
}
