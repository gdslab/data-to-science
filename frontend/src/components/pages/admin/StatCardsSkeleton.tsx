function StatCardSkeleton() {
  return (
    <div className="min-h-[140px] min-w-64 flex flex-col items-center rounded-lg bg-blue-50 px-4 py-8 text-center shadow-md animate-pulse">
      <div className="h-12 w-1/4 text-center bg-gray-300 rounded mb-2"></div>

      <div className="h-6 w-1/2 bg-gray-300 rounded mb-2"></div>
    </div>
  );
}

function StatStorageCardSkeleton() {
  return (
    <div className="min-h-[140px] min-w-64 flex flex-col items-center rounded-lg bg-blue-50 px-4 py-8 text-center shadow-md animate-pulse">
      <div className="h-4 w-full bg-gray-300 rounded-full mb-4"></div>
      <div className="h-6 w-1/2 bg-gray-300 rounded mb-2"></div>
      <div className="h-4 w-full bg-gray-300 rounded mb-2"></div>
    </div>
  );
}

export default function StatCardsSkeleton() {
  return (
    <section className="w-full bg-white">
      <div className="px-4 py-12 sm:px-6 md:py-16 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            Site Statistics
          </h2>

          <p className="mt-4 text-gray-500 sm:text-xl">
            Summary of overall activity on this Data to Science application instance.
          </p>
        </div>

        {/* general summary of users, projects, flights, and data products */}
        <div className="mt-8 sm:mt-12">
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </dl>
        </div>

        {/* data product by data type counts */}
        <div className="mt-8 sm:mt-12">
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </dl>
        </div>

        <div className="mt-8 sm:mt-12">
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatStorageCardSkeleton />
          </dl>
        </div>
      </div>
    </section>
  );
}
