import { AxiosResponse, isAxiosError } from 'axios';
import { Link, Params, useLoaderData, useParams } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';

import api from '../../../../api';
import IndoorProjectPageLayout from './IndoorProjectPageLayout';
import {
  IndoorProjectDataPlantAPIResponse,
  IndoorProjectDataVizAPIResponse,
  IndoorProjectDataVizScatterAPIResponse,
  NumericColumns,
} from './IndoorProject';
import PotGroupModuleDataVisualization from './PotGroupModule/PotGroupModuleDataVisualization';
import TraitScatterModuleDataVisualization from './TraitModule/TraitScatterModuleDataVisualization';
import { fetchTraitScatterModuleVisualizationData } from './TraitModule/scatterService';

export async function loader({ params }: { params: Params<string> }) {
  try {
    // Required ids
    const id = params.indoorProjectId;
    const dId = params.indoorProjectDataId;
    const pId = params.indoorProjectPlantId;

    // Base indoor projects url
    const baseUrl = `/indoor_projects/${id}/uploaded`;

    // Endpoint for fetching plant details
    const plantDetailEndpoint = `${baseUrl}/${dId}/plants/${pId}`;

    // Endpoint for fetching plant chart data
    const plantChartEndpoint = `${baseUrl}/${dId}/data_for_viz`;

    // Query params for top and side chart data
    const plantChartTopQueryParams = {
      camera_orientation: 'top',
      plotted_by: 'pots',
      according_to: 'single_pot',
      pot_barcode: pId,
    };
    const plantChartSideQueryParams = {
      camera_orientation: 'side',
      plotted_by: 'pots',
      according_to: 'single_pot',
      pot_barcode: pId,
    };

    // Endpoint for fetching spreadsheet (numeric columns)
    const spreadsheetEndpoint = `${baseUrl}/${dId}`;

    // Make requests
    const detailResponse: AxiosResponse<IndoorProjectDataPlantAPIResponse> =
      await api.get(plantDetailEndpoint);
    const chartTopResponse: AxiosResponse<IndoorProjectDataVizAPIResponse> =
      await api.get(plantChartEndpoint, { params: plantChartTopQueryParams });
    const chartSideResponse: AxiosResponse<IndoorProjectDataVizAPIResponse> =
      await api.get(plantChartEndpoint, {
        params: plantChartSideQueryParams,
      });
    const spreadsheetResponse = await api.get(spreadsheetEndpoint);

    // Get data from responses
    const detailData = detailResponse.data;
    const chartTopData = chartTopResponse.data;
    const chartSideData = chartSideResponse.data;
    const numericColumns: NumericColumns =
      spreadsheetResponse.data.numeric_columns;

    // Return results
    return {
      ...detailData,
      topChart: chartTopData,
      sideChart: chartSideData,
      numericColumns,
    };
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
  numericColumns: NumericColumns;
}

export default function IndoorProjectPlantDetail() {
  const indoorProjectPlant = useLoaderData() as PlantDetailAndChart;
  const { indoorProjectId, indoorProjectDataId, indoorProjectPlantId } =
    useParams();

  // Local state for single-plant trait scatter
  const [cameraOrientation, setCameraOrientation] = useState<'top' | 'side'>(
    'top'
  );
  const [traitX, setTraitX] = useState<string>('');
  const [traitY, setTraitY] = useState<string>('');
  const [isSubmittingScatter, setIsSubmittingScatter] = useState(false);
  const [scatterData, setScatterData] =
    useState<IndoorProjectDataVizScatterAPIResponse | null>(null);

  if (
    !indoorProjectPlant.ppew ||
    !indoorProjectPlant.topChart ||
    !indoorProjectPlant.sideChart
  )
    return null;

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

  // Derive numeric columns based on orientation
  const availableTraits = useMemo(() => {
    return cameraOrientation === 'top'
      ? indoorProjectPlant.numericColumns.top
      : indoorProjectPlant.numericColumns.side;
  }, [cameraOrientation, indoorProjectPlant.numericColumns]);

  // Initialize default traits when available
  useEffect(() => {
    if (availableTraits.length > 1) {
      setTraitX((prev) => prev || availableTraits[0]);
      setTraitY((prev) => prev || availableTraits[1]);
    } else if (availableTraits.length === 1) {
      setTraitX((prev) => prev || availableTraits[0]);
      setTraitY((prev) => prev || availableTraits[0]);
    }
  }, [availableTraits]);

  async function handleGenerateScatter(e: React.FormEvent) {
    e.preventDefault();
    if (
      !indoorProjectId ||
      !indoorProjectDataId ||
      !traitX ||
      !traitY ||
      !indoorProjectPlantId
    )
      return;

    try {
      setIsSubmittingScatter(true);
      const data = await fetchTraitScatterModuleVisualizationData({
        indoorProjectId,
        indoorProjectDataId,
        cameraOrientation,
        plottedBy: 'pots',
        accordingTo: 'single_pot',
        targetTraitX: traitX,
        targetTraitY: traitY,
        potBarcode: Number(indoorProjectPlantId),
      });

      setScatterData(data);
    } catch (err) {
      console.error('Failed to generate scatter plot', err);
      setScatterData(null);
    } finally {
      setIsSubmittingScatter(false);
    }
  }

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
        {/* Single-plant trait scatter */}
        <div>
          <h2>Trait scatter (single plant)</h2>
          <form
            className="flex flex-col gap-3"
            onSubmit={handleGenerateScatter}
          >
            <div className="flex gap-4 items-center">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="cameraOrientation"
                  value="top"
                  checked={cameraOrientation === 'top'}
                  onChange={() => setCameraOrientation('top')}
                />
                <span>Top</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="cameraOrientation"
                  value="side"
                  checked={cameraOrientation === 'side'}
                  onChange={() => setCameraOrientation('side')}
                />
                <span>Side</span>
              </label>
            </div>
            <div className="flex gap-4 flex-wrap">
              <label className="flex flex-col gap-1 min-w-56">
                <span>X trait</span>
                <select
                  className="p-2 rounded border border-gray-300"
                  value={traitX}
                  onChange={(e) => setTraitX(e.target.value)}
                >
                  {availableTraits.map((t) => (
                    <option key={`x-${t}`} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1 min-w-56">
                <span>Y trait</span>
                <select
                  className="p-2 rounded border border-gray-300"
                  value={traitY}
                  onChange={(e) => setTraitY(e.target.value)}
                >
                  {availableTraits.map((t) => (
                    <option key={`y-${t}`} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div>
              <button
                type="submit"
                disabled={isSubmittingScatter || availableTraits.length < 2}
                className="px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-blue-500/60 disabled:cursor-not-allowed"
              >
                {isSubmittingScatter ? 'Generating...' : 'Generate scatter'}
              </button>
            </div>
          </form>
          {scatterData && scatterData.results.length > 0 && (
            <div className="mt-4">
              <TraitScatterModuleDataVisualization data={scatterData} />
            </div>
          )}
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
