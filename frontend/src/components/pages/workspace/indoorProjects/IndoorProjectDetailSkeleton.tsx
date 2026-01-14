export default function IndoorProjectDetailSkeleton() {
  return (
    <div className="w-full flex flex-col gap-4" aria-busy="true">
      {/* Header section placeholders */}
      <div className="flex flex-col gap-2">
        {/* "Pots" heading skeleton */}
        <div className="h-6 w-32 bg-slate-100 rounded animate-pulse"></div>
        {/* Planting date skeleton */}
        <div className="h-4 w-48 bg-slate-100 rounded animate-pulse"></div>
      </div>

      {/* Tab navigation skeleton */}
      <div className="flex space-x-1 rounded-xl bg-gray-800 p-1">
        <div className="w-full rounded-lg h-10 bg-gray-700 animate-pulse"></div>
        <div className="w-full rounded-lg h-10 bg-gray-700 animate-pulse"></div>
        <div className="w-full rounded-lg h-10 bg-gray-700 animate-pulse"></div>
        <div className="w-full rounded-lg h-10 bg-gray-700 animate-pulse"></div>
      </div>

      {/* Content area skeleton */}
      <div className="rounded-xl bg-gray-50 p-4">
        <div className="h-64 bg-slate-100 rounded animate-pulse flex items-center justify-center">
          <span
            className="text-gray-500 text-sm"
            role="status"
            aria-live="polite"
          >
            Loading project data...
          </span>
        </div>
      </div>
    </div>
  );
}