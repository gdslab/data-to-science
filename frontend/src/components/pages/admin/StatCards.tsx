import StatCard, { StatStorageCard } from './StatCard';

import { SiteStatistics } from './DashboardTypes';

export default function StatCards({ stats }: { stats: SiteStatistics }) {
  return (
    <section className="w-full bg-white">
      <div className="mx-auto max-w-screen-xl px-4 py-12 sm:px-6 md:py-16 lg:px-8">
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
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <StatCard title="Total Users" value={stats.user_count} />
            <StatCard title="Total Projects" value={stats.project_count} />
            <StatCard title="Total Flights" value={stats.flight_count} />
            <StatCard title="Total Data Products" value={stats.data_product_count} />
          </dl>
        </div>

        {/* data product by data type counts */}
        <div className="mt-8 sm:mt-12">
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <StatCard
              title="Total DSM"
              value={stats.data_product_dtype_count.dsm_count}
            />
            <StatCard
              title="Total Ortho"
              value={stats.data_product_dtype_count.ortho_count}
            />
            <StatCard
              title="Total Point Cloud"
              value={stats.data_product_dtype_count.point_cloud_count}
            />
            <StatCard
              title="Total Other"
              value={stats.data_product_dtype_count.other_count}
            />
          </dl>
        </div>

        <div className="mt-8 sm:mt-12">
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <StatStorageCard
              title="Storage (GB)"
              storage={stats.storage_availability}
            />
          </dl>
        </div>
      </div>
    </section>
  );
}
