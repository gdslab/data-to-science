import { Fragment } from 'react';

export default function PotreeViewer({ copcPath }: { copcPath: string }) {
  // Detect mobile device outside of iframe content
  const isMobile =
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    ) || window.innerWidth < 768;

  // Construct the URL to the backend endpoint that serves the Potree viewer
  const potreeViewerUrl = `/potree-viewer?copc_path=${encodeURIComponent(
    copcPath
  )}&is_mobile=${isMobile}`;

  return (
    <Fragment>
      <iframe
        className="h-full w-full touch-none"
        src={potreeViewerUrl}
        sandbox="allow-same-origin allow-scripts allow-popups allow-pointer-lock allow-modals allow-forms"
      ></iframe>
    </Fragment>
  );
}
