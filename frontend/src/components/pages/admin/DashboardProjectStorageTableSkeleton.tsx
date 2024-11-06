export default function DashboardProjectStorageTableSkeleton() {
  return (
    <div className="relative mt-12">
      <table className="relative w-full border-separate border-spacing-y-1 border-spacing-x-1">
        <thead>
          <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
            <th className="p-4">Name</th>
            <th className="p-4">Total projects</th>
            <th className="p-4">Total storage (GB)</th>
          </tr>
        </thead>
        <tbody className="max-h-96 overflow-y-auto">
          {new Array(5).fill(0).map((_, idx) => (
            <tr key={idx} className="text-center">
              <td className="p-4 bg-slate-100 h-14 w-96 animate-pulse"></td>
              <td className="p-4 bg-slate-50 h-14 w-40 animate-pulse"></td>
              <td className="p-4 bg-slate-50 h-14 w-40 animate-pulse"></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
