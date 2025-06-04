import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { GeoJSONFeature } from './Project';

interface ProjectBoundaryDownloadButtonProps {
  field: GeoJSONFeature;
  projectTitle: string;
}

export default function ProjectBoundaryDownloadButton({
  field,
  projectTitle,
}: ProjectBoundaryDownloadButtonProps) {
  if (!field) return null;

  // Sanitize the project title to be safe for filenames
  const sanitizedTitle = projectTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase();

  return (
    <button
      onClick={() => {
        const blob = new Blob([JSON.stringify(field, null, 2)], {
          type: 'application/geo+json',
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${sanitizedTitle}_boundary.geojson`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }}
      className="h-6 w-6 cursor-pointer"
      title="Download Project Boundary"
    >
      <ArrowDownTrayIcon className="h-6 w-6" />
      <span className="sr-only">Download Project Boundary</span>
    </button>
  );
}
