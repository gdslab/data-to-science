export default function DashboardProjectStorageTableSkeleton() {
  return (
    <div className="relative mt-12 flex flex-col gap-4">
      <div className="h-10 w-full animate-pulse rounded-md bg-slate-100"></div>

      <table className="relative hidden w-full border-separate border-spacing-y-1 border-spacing-x-1 md:table">
        <thead>
          <tr className="h-12 text-slate-700 bg-slate-300">
            <th className="p-2 w-16">#</th>
            <th className="p-2">Name</th>
            <th className="p-2">Projects</th>
            <th className="p-2">Storage (GB)</th>
          </tr>
        </thead>
        <tbody>
          {new Array(10).fill(0).map((_, idx) => (
            <tr key={idx} className="text-center">
              <td className="p-2 bg-slate-100 h-14 w-16 animate-pulse"></td>
              <td className="p-2 bg-slate-100 h-14 w-96 animate-pulse"></td>
              <td className="p-2 bg-slate-50 h-14 w-44 animate-pulse"></td>
              <td className="p-2 bg-slate-50 h-14 w-48 animate-pulse"></td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flex flex-col gap-3 md:hidden">
        {new Array(3).fill(0).map((_, idx) => (
          <div
            key={idx}
            className="h-28 animate-pulse rounded-sm bg-slate-100"
          ></div>
        ))}
      </div>
    </div>
  );
}
