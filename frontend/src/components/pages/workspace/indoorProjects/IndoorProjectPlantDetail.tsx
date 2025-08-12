import { AxiosResponse, isAxiosError } from 'axios';
import { Link, Params, useLoaderData, useParams } from 'react-router-dom';

import api from '../../../../api';
import IndoorProjectPageLayout from './IndoorProjectPageLayout';
import {
  IndoorProjectDataPlantAPIResponse,
  IndoorProjectDataVizAPIResponse,
} from './IndoorProject';
import PotGroupModuleDataVisualization from './PotGroupModule/PotGroupModuleDataVisualization';

export async function loader({ params }: { params: Params<string> }) {
  try {
    // Required ids
    const id = params.indoorProjectId;
    const dId = params.indoorProjectDataId;
    const pId = params.indoorProjectPlantId;

    // Base indoor projects url
    const rootApi = import.meta.env.VITE_API_V1_STR;
    const baseUrl = `${rootApi}/indoor_projects/${id}/uploaded`;

    // Endpoint for fetching plant details
    const plantDetailEndpoint = `${baseUrl}/${dId}/plants/${pId}`;

    // Endpoint for fetching plant chart data
    const plantChartEndpoint = `${baseUrl}/${dId}/data_for_viz`;

    // Query params for top and side chart data
    const plantChartTopQueryParams = {
      camera_orientation: 'top',
      group_by: 'treatment',
      pot_barcode: pId,
    };
    const plantChartSideQueryParams = {
      camera_orientation: 'side',
      group_by: 'treatment',
      pot_barcode: pId,
    };

    // Make requests
    const detailResponse: AxiosResponse<IndoorProjectDataPlantAPIResponse> =
      await api.get(plantDetailEndpoint);
    const chartTopResponse: AxiosResponse<IndoorProjectDataVizAPIResponse> =
      await api.get(plantChartEndpoint, { params: plantChartTopQueryParams });
    const chartSideResponse: AxiosResponse<IndoorProjectDataVizAPIResponse> =
      await api.get(plantChartEndpoint, {
        params: plantChartSideQueryParams,
      });

    // Get data from responses
    const detailData = detailResponse.data;
    const chartTopData = chartTopResponse.data;
    const chartSideData = chartSideResponse.data;

    // Return results
    return { ...detailData, topChart: chartTopData, sideChart: chartSideData };
  } catch (error) {
    if (isAxiosError(error)) {
      // Axios-specific error handling
      const status = error.response?.status || 500;
      const message = error.response?.data?.message || error.message;

      throw {
        status,
        message: `Failed to fetch plant data: ${message}`,
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

const HeaderCell = ({ children }: { children: React.ReactNode }) => (
  <th className="p-2">{children}</th>
);

const Cell = ({
  children,
  extraStyles = '',
}: {
  children: React.ReactNode;
  extraStyles?: string;
}) => <td className={`mx-1 my-2 p-2 bg-white ${extraStyles}`}>{children}</td>;

interface PlantDetailAndChart extends IndoorProjectDataPlantAPIResponse {
  topChart: IndoorProjectDataVizAPIResponse;
  sideChart: IndoorProjectDataVizAPIResponse;
}

export default function IndoorProjectPlantDetail() {
  const indoorProjectPlant = useLoaderData() as PlantDetailAndChart;

  const { indoorProjectId } = useParams();

  if (
    !indoorProjectPlant.ppew ||
    !indoorProjectPlant.topChart ||
    !indoorProjectPlant.sideChart
  )
    return null;

  console.log(indoorProjectPlant);

  const topImages: Record<string, string[]> = indoorProjectPlant.top.reduce(
    (acc, { dfp, images }) => ({
      ...acc,
      [dfp]: images,
    }),
    {}
  );

  const sideImages: Record<string, string[]> =
    indoorProjectPlant.side_avg.reduce(
      (acc, { dfp, images }) => ({
        ...acc,
        [dfp]: images,
      }),
      {}
    );

  return (
    <IndoorProjectPageLayout>
      <h1>Plant Details</h1>
      <div className="flex flex-col gap-4">
        {/* Plant detail table */}
        <div className="max-w-full overflow-x-auto">
          <table className="min-w-[600px] w-full border-separate border-spacing-y-1 border-spacing-x-1">
            <thead>
              <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
                {Object.keys(indoorProjectPlant.ppew).map((key) => (
                  <HeaderCell key={key}>{key}</HeaderCell>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                {Object.keys(indoorProjectPlant.ppew).map((key) => (
                  <Cell key={key}>
                    <span title={indoorProjectPlant.ppew[key]}>
                      {indoorProjectPlant.ppew[key]}
                    </span>
                  </Cell>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
        {/* Top chart */}
        <div>
          <h2>Top</h2>
          <PotGroupModuleDataVisualization
            data={indoorProjectPlant.topChart}
            images={topImages}
          />
        </div>
        {/* Side chart */}
        <div>
          <h2>Side average</h2>
          <PotGroupModuleDataVisualization
            data={indoorProjectPlant.sideChart}
            images={sideImages}
          />
        </div>
        <Link to={`/indoor_projects/${indoorProjectId}`}>
          <button
            type="button"
            className="max-h-12 px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-blue-500/60 disabled:cursor-not-allowed"
          >
            Return
          </button>
        </Link>
      </div>
    </IndoorProjectPageLayout>
  );
}
