export default function STACDisabled() {
  return (
    <div className="p-8 text-center">
      <div className="max-w-md mx-auto">
        <svg
          className="h-16 w-16 mx-auto text-gray-400 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1}
            d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L5.636 5.636"
          />
        </svg>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          STAC Publishing Disabled
        </h2>
        <p className="text-gray-600 mb-6">
          STAC (SpatioTemporal Asset Catalog) functionality is currently
          disabled on this instance.
        </p>
        <p className="text-sm text-gray-500">
          Contact your administrator if you need access to this feature.
        </p>
      </div>
    </div>
  );
}
