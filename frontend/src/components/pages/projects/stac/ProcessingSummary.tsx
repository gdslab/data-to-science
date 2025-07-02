import { CombinedSTACItem } from './STACTypes';

interface ProcessingSummaryProps {
  allItems: CombinedSTACItem[];
}

export default function ProcessingSummary({
  allItems,
}: ProcessingSummaryProps) {
  const successfulItems = allItems.filter((item) => item.isSuccessful);
  const failedItems = allItems.filter((item) => !item.isSuccessful);

  return (
    <div className="mb-4 p-3 bg-gray-100 rounded">
      <h4 className="font-semibold mb-2">Processing Summary</h4>
      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-1">
          <svg
            className="w-4 h-4 text-green-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
          <span className="text-green-700 font-medium">
            {successfulItems.length} Successful
          </span>
        </div>
        {failedItems.length > 0 && (
          <div className="flex items-center gap-1">
            <svg
              className="w-4 h-4 text-red-600"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-red-700 font-medium">
              {failedItems.length} Failed
            </span>
          </div>
        )}
      </div>
      {failedItems.length > 0 && (
        <p className="text-yellow-700 text-sm mt-2 bg-yellow-50 p-2 rounded">
          ⚠️ Some items failed to process. They will not be included in the
          published STAC catalog. Please review the error details below.
        </p>
      )}
    </div>
  );
}
