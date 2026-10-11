import { useParams } from 'react-router';
import { FaDownload, FaRegFilePdf } from 'react-icons/fa6';

export default function RawDataDownloadLink({ rawDataId }: { rawDataId: string }) {
  const { flightId, projectId } = useParams();

  return (
    <a
      className="flex items-center gap-1 text-sky-600"
      href={`${
        import.meta.env.VITE_API_V1_STR
      }/projects/${projectId}/flights/${flightId}/raw_data/${rawDataId}/download`}
      download
      title="Download zipped raw data"
    >
      <FaDownload className="w-4 h-4" />
      <span className="text-sm">Download</span>
    </a>
  );
}

export function RawDataReportDownloadLink({ url }: { url: string }) {
  return (
    <a
      className="flex items-center gap-1 text-sky-600"
      href={url}
      download
      title="Download processing report"
    >
      <FaRegFilePdf className="w-4 h-4" />
      <span className="text-sm">Report</span>
    </a>
  );
}
