import { Fragment, useMemo } from 'react';
import { useLocation } from 'react-router-dom';

import { AlertBar } from '../Alert';

function useQuery() {
  const { search } = useLocation();

  return useMemo(() => new URLSearchParams(search), [search]);
}

export default function SharePotreeViewer() {
  const query = useQuery();
  const fileID = query.get('file_id');

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
