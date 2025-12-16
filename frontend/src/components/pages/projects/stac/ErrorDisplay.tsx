import { XCircleIcon } from '@heroicons/react/24/outline';

import { STACMetadata } from './STACTypes';

interface ErrorDisplayProps {
  stacMetadata: STACMetadata | null;
  onRetry: () => void;
}

export default function ErrorDisplay({
  stacMetadata,
  onRetry,
}: ErrorDisplayProps) {
  if (!stacMetadata || !('error' in stacMetadata)) return null;

  const errorMessage = String(stacMetadata.error);
  const isNoFlightsError = errorMessage.includes(
    'must have at least one flight'
  );

  return (
    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <div className="flex items-center">
        <XCircleIcon className="w-5 h-5 mr-2 text-red-600" />
        <span className="text-red-800 font-medium">
          {isNoFlightsError
            ? 'No Data Available for Publishing'
            : 'Error generating STAC metadata'}
        </span>
      </div>
      <p className="text-sm text-red-600 mt-1">{errorMessage}</p>
      {isNoFlightsError && (
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-sm">
          <p className="text-blue-800 text-sm">
            <strong>To publish this project:</strong>
          </p>
          <ul className="text-blue-700 text-sm mt-1 ml-4 list-disc">
            <li>Add at least one flight to your project</li>
            <li>Upload a data product or process raw data for the flight(s)</li>
            <li>Ensure data products have been processed successfully</li>
          </ul>
        </div>
      )}
      {!isNoFlightsError && (
        <button
          onClick={onRetry}
          className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded-sm hover:bg-red-200"
        >
          Retry
        </button>
      )}
    </div>
  );
}
