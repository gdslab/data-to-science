import { AxiosResponse, isAxiosError } from 'axios';
import { Suspense } from 'react';
import {
  Await,
  isRouteErrorResponse,
  useLoaderData,
  useRouteError,
} from 'react-router-dom';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

import { SiteStatistics } from './DashboardTypes';
import StatCards from './StatCards';
import StatCardsSkeleton from './StatCardsSkeleton';

import api from '../../../api';

export async function loader() {
  const endpoint = '/admin/site_statistics';

  try {
    const stats: Promise<AxiosResponse<SiteStatistics>> = api.get(endpoint);

    return { stats };
  } catch (error) {
    if (isAxiosError(error)) {
      // Axios-specific error handling
      const status = error.response?.status || 500;
      const message = error.response?.data?.message || error.message;

      throw {
        status,
        message: `Failed to load site statistics: ${message}`,
      };
    } else {
      // Generic error handling
      throw {
        status: 500,
        message: 'An unexpected error occurred.',
      };
    }
  }
}

type LoaderError = {
  status: number;
  message: string;
};

function ErrorElement() {
  const error = useRouteError() as LoaderError;

  return (
    <div className="h-full w-full flex flex-col items-center justify-center">
      <ExclamationTriangleIcon className="h-10 w-10 text-red-600" />
      <span className="text-2xl font-semibold text-primary">
        {isRouteErrorResponse(error)
          ? error.data.message
          : 'Something went wrong!'}
      </span>
    </div>
  );
}

export default function DashboardSiteStatistics() {
  const { stats } = useLoaderData() as { stats: Promise<SiteStatistics> };

  return (
    <Suspense fallback={<StatCardsSkeleton />}>
      <Await resolve={stats} errorElement={<ErrorElement />}>
        {(resolvedStats) => <StatCards stats={resolvedStats.data} />}
      </Await>
    </Suspense>
  );
}
