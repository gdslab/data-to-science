import axios, { AxiosResponse } from 'axios';
import { Suspense } from 'react';
import { Await, defer, useLoaderData } from 'react-router-dom';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

import DashboardProjectStorageTable from './DashboardProjectStorageTable';
import { ProjectStatistics } from './DashboardTypes';
import DashboardProjectStorageTableSkeleton from './DashboardProjectStorageTableSkeleton';

export async function loader() {
  const response: Promise<AxiosResponse<ProjectStatistics[]>> = axios.get(
    `${import.meta.env.VITE_API_V1_STR}/admin/project_statistics`
  );
  return defer({ response });
}

function ErrorElement() {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center">
      <ExclamationTriangleIcon className="h-10 w-10 text-red-600" />
      <span className="text-2xl font-semibold text-primary">
        Error occurred. Unable to load user project statistics.
      </span>
    </div>
  );
}

export default function DashboardProjectStorage() {
  const projectStatisticsApiResponse = useLoaderData() as {
    response: Promise<ProjectStatistics[]>;
  };

  return (
    <section className="w-full bg-white">
      <div className="h-full mx-auto max-w-screen-xl px-4 py-12 sm:px-6 md:py-16 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            User Project Storage
          </h2>
          <p className="mt-4 text-gray-500 sm:text-xl">
            Summary of total disk usage by user based on project ownership.
          </p>
          <Suspense fallback={<DashboardProjectStorageTableSkeleton />}>
            <Await
              resolve={projectStatisticsApiResponse.response}
              errorElement={<ErrorElement />}
            >
              {(response) => (
                <DashboardProjectStorageTable userProjectStats={response.data} />
              )}
            </Await>
          </Suspense>
        </div>
      </div>
    </section>
  );
}
