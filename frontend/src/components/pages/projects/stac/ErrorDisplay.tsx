import { XCircleIcon } from '@heroicons/react/24/outline';

interface ErrorDisplayProps {
  stacMetadata: any;
  onRetry: () => void;
}

export default function ErrorDisplay({
  stacMetadata,
  onRetry,
}: ErrorDisplayProps) {
  if (!stacMetadata || !('error' in stacMetadata)) return null;

  return (
    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <div className="flex items-center">
        <XCircleIcon className="w-5 h-5 mr-2 text-red-600" />
        <span className="text-red-800 font-medium">
          Error generating STAC metadata
        </span>
      </div>
      <p className="text-sm text-red-600 mt-1">{String(stacMetadata.error)}</p>
      <button
        onClick={onRetry}
        className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
      >
        Retry
      </button>
    </div>
  );
}
