import { useParams } from 'react-router';
import { ArrowDownTrayIcon, DocumentIcon } from '@heroicons/react/24/outline';

export default function RawDataDownloadLink({ rawDataId }: { rawDataId: string }) {
  const { flightId, projectId } = useParams();

  return (
    <a
      className="flex items-center gap-1 text-sky-600"
      href={`${
        import.meta.env.VITE_API_V1_STR
      }/projects/${projectId}/flights/${flightId}/raw_data/${rawDataId}/download`}
      download
    >
      <ArrowDownTrayIcon
        className="w-4 h-4"
        title="Download zipped raw data"
      />
      <span className="text-sm">Download</span>
    </a>
  );
}

export function RawDataReportDownloadLink({ url }: { url: string }) {
  return (
    <a className="flex items-center gap-1 text-sky-600" href={url} download>
      <DocumentIcon className="w-4 h-4" title="Download processing report" />
      <span className="text-sm">Report</span>
    </a>
  );
}
