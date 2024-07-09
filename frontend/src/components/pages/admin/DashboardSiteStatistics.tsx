import axios, { AxiosResponse } from 'axios';
import { Suspense } from 'react';
import { Await, defer, useLoaderData } from 'react-router-dom';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

import StatCards from './StatCards';

import { SiteStatistics } from './DashboardTypes';
import StatCardsSkeleton from './StatCardsSkeleton';

export async function loader() {
  const response: Promise<AxiosResponse<SiteStatistics>> = axios.get(
    `${import.meta.env.VITE_API_V1_STR}/admin/site_statistics`
  );
  if (response) {
    return defer({ stats: response });
  } else {
    return [];
  }
}

function ErrorElement() {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center">
      <ExclamationTriangleIcon className="h-10 w-10 text-red-600" />
      <span className="text-2xl font-semibold text-primary">
        Error occurred. Unable to load statistics.
      </span>
    </div>
  );
}

export default function DashboardSiteStatistics() {
  const data = useLoaderData() as { stats: Promise<SiteStatistics> };

  return (
    <Suspense fallback={<StatCardsSkeleton />}>
      <Await resolve={data.stats} errorElement={<ErrorElement />}>
        {(stats) => <StatCards stats={stats.data} />}
      </Await>
    </Suspense>
  );
}
