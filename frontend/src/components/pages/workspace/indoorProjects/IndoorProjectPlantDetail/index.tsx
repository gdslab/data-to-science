import { Suspense } from 'react';
import { Await, Link, useLoaderData, useParams } from 'react-router';

import PlantDetailsTable from './components/PlantDetailsTable';
import TopChart from './components/TopChart';
import SideChart from './components/SideChart';
import TraitScatterSection from './components/TraitScatterSection';
import PlantDetailsSkeleton from './components/skeletons/PlantDetailsSkeleton';
import ChartSkeleton from './components/skeletons/ChartSkeleton';

import { PlantDetailAndChart } from './types';

export { loader } from './loader';

export default function IndoorProjectPlantDetail() {
  const { plantData } = useLoaderData() as {
    plantData: Promise<PlantDetailAndChart>;
  };

  return (
    <div className="h-full mx-4 py-2 flex flex-col gap-2">
      <h1>Plant Details</h1>
      <div className="flex flex-col gap-4">
        {/* Plant detail table */}
        <div className="max-w-full overflow-x-auto">
          <Suspense fallback={<PlantDetailsSkeleton />}>
            <Await resolve={plantData}>
              {(data) => (
                <PlantDetailsTable data={data as PlantDetailAndChart} />
              )}
            </Await>
          </Suspense>
        </div>
        {/* Top chart */}
        <div>
          <h2>Top</h2>
          <Suspense fallback={<ChartSkeleton />}>
            <Await resolve={plantData}>
              {(data) => <TopChart data={data as PlantDetailAndChart} />}
            </Await>
          </Suspense>
        </div>
        {/* Side chart */}
        <div>
          <h2>Side average</h2>
          <Suspense fallback={<ChartSkeleton />}>
            <Await resolve={plantData}>
              {(data) => <SideChart data={data as PlantDetailAndChart} />}
            </Await>
          </Suspense>
        </div>
        {/* Single-plant trait scatter */}
        <Suspense fallback={null}>
          <Await resolve={plantData}>
            {(data) => (
              <TraitScatterSection data={data as PlantDetailAndChart} />
            )}
          </Await>
        </Suspense>
        <ReturnButton />
      </div>
    </div>
  );
}

function ReturnButton() {
  const { indoorProjectId } = useParams();
  return (
    <Link to={`/indoor_projects/${indoorProjectId}`}>
      <button
        type="button"
        className="max-h-12 px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-blue-500/60 disabled:cursor-not-allowed"
      >
        Return
      </button>
    </Link>
  );
}
