import { CombinedSTACItem } from './STACTypes';

interface ItemsListProps {
  allItems: CombinedSTACItem[];
}

export default function ItemsList({ allItems }: ItemsListProps) {
  return (
    <div>
      <h4 className="font-semibold mb-2">Items ({allItems.length})</h4>
      <div className="ml-4 max-h-96 overflow-y-auto">
        {allItems.map((item) => (
          <div
            key={item.id}
            className={`mb-2 p-2 rounded border shadow-sm ${
              item.isSuccessful
                ? 'bg-white border-gray-200'
                : 'bg-red-50 border-red-200'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  {item.isSuccessful ? (
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
                  ) : (
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
                  )}
                  <span className="font-medium text-sm">
                    {item.isSuccessful ? 'Success' : 'Failed'}
                  </span>
                </div>
                <p>
                  <span className="font-medium">ID:</span> {item.id}
                </p>
                {item.isSuccessful ? (
                  <>
                    {item.title && (
                      <p>
                        <span className="font-medium">Title:</span> {item.title}
                      </p>
                    )}
                    {item.browserUrl && (
                      <p>
                        <a
                          href={item.browserUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 underline"
                        >
                          STAC link
                        </a>
                      </p>
                    )}
                    <p>
                      <span className="font-medium">Data Type:</span>{' '}
                      {item.dataType}
                    </p>
                    <p>
                      <span className="font-medium">Acquisition Date:</span>{' '}
                      {item.acquisitionDate &&
                        new Date(item.acquisitionDate).toLocaleDateString()}
                    </p>
                    <p>
                      <span className="font-medium">Platform:</span>{' '}
                      {item.platform?.replace(/_/g, ' ')}
                    </p>
                    <p>
                      <span className="font-medium">Sensor:</span> {item.sensor}
                    </p>
                  </>
                ) : (
                  <div className="mt-2">
                    {/* Display item details for failed items */}
                    {item.error?.details?.title && (
                      <p>
                        <span className="font-medium">Title:</span>{' '}
                        {item.error.details.title}
                      </p>
                    )}
                    <p>
                      <span className="font-medium">Data Type:</span>{' '}
                      {item.error?.details?.data_type || 'Unknown'}
                    </p>
                    {item.error?.details?.acquisition_date && (
                      <p>
                        <span className="font-medium">Acquisition Date:</span>{' '}
                        {new Date(
                          item.error.details.acquisition_date
                        ).toLocaleDateString()}
                      </p>
                    )}
                    {item.error?.details?.platform && (
                      <p>
                        <span className="font-medium">Platform:</span>{' '}
                        {item.error.details.platform.replace(/_/g, ' ')}
                      </p>
                    )}
                    {item.error?.details?.sensor && (
                      <p>
                        <span className="font-medium">Sensor:</span>{' '}
                        {item.error.details.sensor}
                      </p>
                    )}

                    {/* Error information */}
                    <div className="mt-3 pt-2 border-t border-red-200">
                      <p className="text-red-700 font-medium">
                        Error: {item.error?.code || 'Unknown error'}
                      </p>
                      <p className="text-red-600 text-sm mt-1">
                        {item.error?.message || 'No error message available'}
                      </p>
                      {item.error?.details && (
                        <details className="mt-2">
                          <summary className="text-sm text-gray-600 cursor-pointer">
                            Technical Details
                          </summary>
                          <div className="mt-1 text-xs text-gray-500 bg-gray-50 p-2 rounded">
                            <p>
                              <strong>File Path:</strong>{' '}
                              {item.error.details.filepath}
                            </p>
                            <p>
                              <strong>Flight ID:</strong>{' '}
                              {item.error.details.flight_id}
                            </p>
                            <p>
                              <strong>Timestamp:</strong>{' '}
                              {new Date(item.error.timestamp).toLocaleString()}
                            </p>
                          </div>
                        </details>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
