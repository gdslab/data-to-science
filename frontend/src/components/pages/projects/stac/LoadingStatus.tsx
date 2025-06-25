import { ArrowPathIcon } from '@heroicons/react/24/outline';

interface LoadingStatusProps {
  isGeneratingPreview: boolean;
  stacMetadata: any;
  pollingStatus: string;
}

export default function LoadingStatus({
  isGeneratingPreview,
  stacMetadata,
  pollingStatus,
}: LoadingStatusProps) {
  if (!isGeneratingPreview && stacMetadata) return null;

  return (
    <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex items-center">
        <ArrowPathIcon className="w-5 h-5 mr-2 animate-spin text-blue-600" />
        <span className="text-blue-800">
          {isGeneratingPreview
            ? 'Generating STAC metadata...'
            : 'Loading STAC metadata...'}
        </span>
      </div>
      <p className="text-sm text-blue-600 mt-1">
        This may take a few moments for large datasets.
      </p>
      {pollingStatus && (
        <p className="text-xs text-blue-500 mt-2 font-mono">{pollingStatus}</p>
      )}
    </div>
  );
}
