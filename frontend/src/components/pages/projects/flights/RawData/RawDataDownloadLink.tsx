import { useParams } from 'react-router-dom';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

export default function RawDataDownloadLink({ rawDataId }: { rawDataId: string }) {
  const { flightId, projectId } = useParams();

  return (
    <a
      href={`${
        import.meta.env.VITE_API_V1_STR
      }/projects/${projectId}/flights/${flightId}/raw_data/${rawDataId}/download`}
      download
    >
      <span className="sr-only">Download</span>
      <ArrowDownTrayIcon className="h-5 w-5 hover:scale-110" />
    </a>
  );
}
