import LoadingStatus from '../LoadingStatus';
import ErrorDisplay from '../ErrorDisplay';
import { STACMetadata } from '../STACTypes';

interface STACStatusIndicatorsProps {
  isGenerating: boolean;
  isChecking: boolean;
  stacMetadata: STACMetadata | null;
  pollingStatus: string;
  onRetry: () => void;
}

export default function STACStatusIndicators({
  isGenerating,
  isChecking,
  stacMetadata,
  pollingStatus,
  onRetry,
}: STACStatusIndicatorsProps) {
  return (
    <>
      <LoadingStatus
        isGeneratingPreview={isGenerating}
        stacMetadata={stacMetadata}
        pollingStatus={pollingStatus}
      />

      <ErrorDisplay stacMetadata={stacMetadata} onRetry={onRetry} />

      {/* Background update check indicator */}
      {isChecking && (
        <div className="mb-4 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center text-xs">
            <svg
              className="w-3 h-3 mr-2 animate-spin text-blue-600"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span className="text-blue-700">Checking for updates...</span>
          </div>
        </div>
      )}
    </>
  );
}
