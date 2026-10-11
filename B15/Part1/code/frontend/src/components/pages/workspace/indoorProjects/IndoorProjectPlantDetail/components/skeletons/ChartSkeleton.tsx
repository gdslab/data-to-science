export default function ChartSkeleton() {
  return (
    <div
      className="w-full h-40 bg-slate-100 rounded animate-pulse flex items-center justify-center"
      aria-busy="true"
    >
      <span className="text-gray-500 text-sm" role="status" aria-live="polite">
        Please wait while we fetch the plant data
      </span>
    </div>
  );
}
