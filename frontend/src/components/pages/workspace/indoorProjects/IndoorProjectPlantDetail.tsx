import axios, { AxiosResponse, isAxiosError } from 'axios';
import { Link, Params, useLoaderData, useParams } from 'react-router-dom';

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
      await axios.get(plantDetailEndpoint);
    const chartTopResponse: AxiosResponse<IndoorProjectDataVizAPIResponse> =
      await axios.get(plantChartEndpoint, { params: plantChartTopQueryParams });
    const chartSideResponse: AxiosResponse<IndoorProjectDataVizAPIResponse> =
      await axios.get(plantChartEndpoint, {
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

// function IndoorProjectDetailOld() {
//   const { indoorProjectId, indoorProjectDataId } = useParams();

//   const indoorProjectPlant =
//     useLoaderData() as IndoorProjectDataPlantAPIResponse;

//   const sortedTopData = useMemo(() => {
//     if (indoorProjectPlant.top.length > 0) {
//       const sorted = indoorProjectPlant.top.sort((a, b) => {
//         const scanDateA = new Date(a.scan_date).getTime();
//         const scanDateB = new Date(b.scan_date).getTime();

//         return scanDateA - scanDateB;
//       });

//       return sorted;
//     } else {
//       return [];
//     }
//   }, [indoorProjectPlant.top]);

//   const sortedSideData = useMemo(() => {
//     if (indoorProjectPlant.side_all.length > 0) {
//       const sorted = indoorProjectPlant.side_all.sort((a, b) => {
//         const scanDateA = new Date(a.scan_date);
//         const scanDateB = new Date(b.scan_date);

//         if (scanDateA < scanDateB) return -1;
//         if (scanDateA > scanDateB) return 1;

//         // if scan dates are the same, sort by frame_nr
//         return a.frame_nr - b.frame_nr;
//       });

//       return sorted;
//     } else {
//       return [];
//     }
//   }, [indoorProjectPlant.side_all]);

//   const sortedSideAvgData = useMemo(() => {
//     return indoorProjectPlant.side_avg;
//   }, [indoorProjectPlant.side_avg]);

//   console.log(indoorProjectPlant);

//   return (
//     <IndoorProjectPageLayout>
//       <h1>Plant Details</h1>
//       <pre className="whitespace-pre-wrap p-10 border-2 border-slate-600">
//         {JSON.stringify(indoorProjectPlant.ppew, null, 2)}
//       </pre>

//       <h2>Top</h2>
//       {sortedTopData.length > 0 && (
//         <div className="max-w-full overflow-x-auto">
//           <table className="min-w-[600px] w-full border-separate border-spacing-y-1 border-spacing-x-1">
//             <thead>
//               <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
//                 <HeaderCell>Filename</HeaderCell>
//                 <HeaderCell>Exp ID</HeaderCell>
//                 <HeaderCell>Pot Barcode</HeaderCell>
//                 <HeaderCell>Variety</HeaderCell>
//                 <HeaderCell>Treatment</HeaderCell>
//                 <HeaderCell>Scan Time</HeaderCell>
//                 <HeaderCell>Scan Date</HeaderCell>
//                 <HeaderCell>DFP</HeaderCell>
//                 <HeaderCell>Angle</HeaderCell>
//                 <HeaderCell>Surface</HeaderCell>
//                 <HeaderCell>Convex Hull</HeaderCell>
//                 <HeaderCell>Roundness</HeaderCell>
//                 <HeaderCell>Center of mass distance</HeaderCell>
//                 <HeaderCell>Center of mass x</HeaderCell>
//                 <HeaderCell>Center of mass y</HeaderCell>
//                 <HeaderCell>Hue</HeaderCell>
//                 <HeaderCell>Saturation</HeaderCell>
//                 <HeaderCell>Intensity</HeaderCell>
//                 <HeaderCell>Fluorescence</HeaderCell>
//                 <HeaderCell>Charts</HeaderCell>
//               </tr>
//             </thead>
//             <tbody>
//               {sortedTopData.map((topRecord, index) => (
//                 <tr key={index}>
//                   <Cell extraStyles="max-w-60 truncate">
//                     <span title={topRecord.filename}>{topRecord.filename}</span>
//                   </Cell>
//                   <Cell>{topRecord.exp_id}</Cell>
//                   <Cell>{topRecord.pot_barcode}</Cell>
//                   <Cell>{topRecord.variety}</Cell>
//                   <Cell>{topRecord.treatment}</Cell>
//                   <Cell>{topRecord.scan_time}</Cell>
//                   <Cell>{topRecord.scan_date}</Cell>
//                   <Cell>{topRecord.dfp}</Cell>
//                   <Cell>{topRecord.angle}</Cell>
//                   <Cell>{topRecord.surface}</Cell>
//                   <Cell>{topRecord.convex_hull}</Cell>
//                   <Cell>{topRecord.roundness}</Cell>
//                   <Cell>{topRecord.center_of_mass_distance}</Cell>
//                   <Cell>{topRecord.center_of_mass_x}</Cell>
//                   <Cell>{topRecord.center_of_mass_y}</Cell>
//                   <Cell>{topRecord.hue}</Cell>
//                   <Cell>{topRecord.saturation}</Cell>
//                   <Cell>{topRecord.intensity}</Cell>
//                   <Cell>{topRecord.fluorescence}</Cell>
//                   <Cell>
//                     <div className="flex gap-2">
//                       {topRecord.hue > 0 && (
//                         <ChartModal
//                           data={{
//                             btnLabel: 'H',
//                             label: 'hue',
//                             values: Object.entries(topRecord).filter(
//                               ([key, _value]) => /^h\d+$/.test(key)
//                             ) as [],
//                           }}
//                         />
//                       )}
//                       {topRecord.saturation > 0 && (
//                         <ChartModal
//                           data={{
//                             btnLabel: 'S',
//                             label: 'saturation',
//                             values: Object.entries(topRecord).filter(
//                               ([key, _value]) => /^s\d+$/.test(key)
//                             ) as [],
//                           }}
//                         />
//                       )}
//                       {topRecord.intensity > 0 && (
//                         <ChartModal
//                           data={{
//                             btnLabel: 'V',
//                             label: 'intensity',
//                             values: Object.entries(topRecord).filter(
//                               ([key, _value]) => /^v\d+$/.test(key)
//                             ) as [],
//                           }}
//                         />
//                       )}
//                       {topRecord.fluorescence > 0 && (
//                         <ChartModal
//                           data={{
//                             btnLabel: 'F',
//                             label: 'fluorescence',
//                             values: Object.entries(topRecord).filter(
//                               ([key, _value]) => /^f\d+$/.test(key)
//                             ) as [],
//                           }}
//                         />
//                       )}
//                     </div>
//                   </Cell>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         </div>
//       )}

//       <h2>Side All</h2>
//       {sortedSideData.length > 0 && (
//         <div className="max-w-full overflow-x-auto">
//           <table className="min-w-[600px] w-full border-separate border-spacing-y-1 border-spacing-x-1">
//             <thead>
//               <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
//                 <HeaderCell>Filename</HeaderCell>
//                 <HeaderCell>Exp ID</HeaderCell>
//                 <HeaderCell>Pot Barcode</HeaderCell>
//                 <HeaderCell>Variety</HeaderCell>
//                 <HeaderCell>Treatment</HeaderCell>
//                 <HeaderCell>Scan Time</HeaderCell>
//                 <HeaderCell>Scan Date</HeaderCell>
//                 <HeaderCell>DFP</HeaderCell>
//                 <HeaderCell>View</HeaderCell>
//                 <HeaderCell>Frame NR</HeaderCell>
//                 <HeaderCell>Width</HeaderCell>
//                 <HeaderCell>Height</HeaderCell>
//                 <HeaderCell>Surface</HeaderCell>
//                 <HeaderCell>Convex Hull</HeaderCell>
//                 <HeaderCell>Roundness</HeaderCell>
//                 <HeaderCell>Center of mass distance</HeaderCell>
//                 <HeaderCell>Center of mass x</HeaderCell>
//                 <HeaderCell>Center of mass y</HeaderCell>
//                 <HeaderCell>Hue</HeaderCell>
//                 <HeaderCell>Saturation</HeaderCell>
//                 <HeaderCell>Intensity</HeaderCell>
//                 <HeaderCell>Fluorescence</HeaderCell>
//                 <HeaderCell>Images</HeaderCell>
//               </tr>
//             </thead>
//             <tbody>
//               {sortedSideData.map((sideRecord, index) => (
//                 <tr key={index}>
//                   <Cell extraStyles="max-w-60 truncate">
//                     <span title={sideRecord.filename}>
//                       {sideRecord.filename}
//                     </span>
//                   </Cell>
//                   <Cell>{sideRecord.exp_id}</Cell>
//                   <Cell>{sideRecord.pot_barcode}</Cell>
//                   <Cell>{sideRecord.variety}</Cell>
//                   <Cell>{sideRecord.treatment}</Cell>
//                   <Cell>{sideRecord.scan_time}</Cell>
//                   <Cell>{sideRecord.scan_date}</Cell>
//                   <Cell>{sideRecord.dfp}</Cell>
//                   <Cell>{sideRecord.view}</Cell>
//                   <Cell>{sideRecord.frame_nr}</Cell>
//                   <Cell>{sideRecord.width}</Cell>
//                   <Cell>{sideRecord.height}</Cell>
//                   <Cell>{sideRecord.surface}</Cell>
//                   <Cell>{sideRecord.convex_hull}</Cell>
//                   <Cell>{sideRecord.roundness}</Cell>
//                   <Cell>{sideRecord.center_of_mass_distance}</Cell>
//                   <Cell>{sideRecord.center_of_mass_x}</Cell>
//                   <Cell>{sideRecord.center_of_mass_y}</Cell>
//                   <Cell>{sideRecord.hue}</Cell>
//                   <Cell>{sideRecord.saturation}</Cell>
//                   <Cell>{sideRecord.intensity}</Cell>
//                   <Cell>{sideRecord.fluorescence}</Cell>
//                   <Cell>
//                     {indoorProjectId && indoorProjectDataId && (
//                       <ImageModal
//                         filename={sideRecord.filename}
//                         indoorProjectId={indoorProjectId}
//                         indoorProjectDataId={indoorProjectDataId}
//                       />
//                     )}
//                   </Cell>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         </div>
//       )}

//       <h2>Side Average</h2>
//       {sortedSideAvgData.length > 0 && (
//         <div className="max-w-full overflow-x-auto">
//           <table className="min-w-[600px] w-full border-separate border-spacing-y-1 border-spacing-x-1">
//             <thead>
//               <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
//                 <HeaderCell>Filename</HeaderCell>
//                 <HeaderCell>Exp ID</HeaderCell>
//                 <HeaderCell>Pot Barcode</HeaderCell>
//                 <HeaderCell>Variety</HeaderCell>
//                 <HeaderCell>Treatment</HeaderCell>
//                 <HeaderCell>Scan Time</HeaderCell>
//                 <HeaderCell>Scan Date</HeaderCell>
//                 <HeaderCell>DFP</HeaderCell>
//                 <HeaderCell>View</HeaderCell>
//                 <HeaderCell>Width</HeaderCell>
//                 <HeaderCell>Height</HeaderCell>
//                 <HeaderCell>Surface</HeaderCell>
//                 <HeaderCell>Convex Hull</HeaderCell>
//                 <HeaderCell>Roundness</HeaderCell>
//                 <HeaderCell>Center of mass distance</HeaderCell>
//                 <HeaderCell>Center of mass x</HeaderCell>
//                 <HeaderCell>Center of mass y</HeaderCell>
//                 <HeaderCell>Hue</HeaderCell>
//                 <HeaderCell>Saturation</HeaderCell>
//                 <HeaderCell>Intensity</HeaderCell>
//                 <HeaderCell>Fluorescence</HeaderCell>
//                 <HeaderCell>Images</HeaderCell>
//               </tr>
//             </thead>
//             <tbody>
//               {sortedSideAvgData.map((sideRecord, index) => (
//                 <tr key={index}>
//                   <Cell extraStyles="max-w-60 truncate">
//                     <span title={sideRecord.filename}>
//                       {sideRecord.filename}
//                     </span>
//                   </Cell>
//                   <Cell>{sideRecord.exp_id}</Cell>
//                   <Cell>{sideRecord.pot_barcode}</Cell>
//                   <Cell>{sideRecord.variety}</Cell>
//                   <Cell>{sideRecord.treatment}</Cell>
//                   <Cell>{sideRecord.scan_time}</Cell>
//                   <Cell>{sideRecord.scan_date}</Cell>
//                   <Cell>{sideRecord.dfp}</Cell>
//                   <Cell>{sideRecord.view}</Cell>
//                   <Cell>{sideRecord.width}</Cell>
//                   <Cell>{sideRecord.height}</Cell>
//                   <Cell>{sideRecord.surface}</Cell>
//                   <Cell>{sideRecord.convex_hull}</Cell>
//                   <Cell>{sideRecord.roundness}</Cell>
//                   <Cell>{sideRecord.center_of_mass_distance}</Cell>
//                   <Cell>{sideRecord.center_of_mass_x}</Cell>
//                   <Cell>{sideRecord.center_of_mass_y}</Cell>
//                   <Cell>{sideRecord.hue}</Cell>
//                   <Cell>{sideRecord.saturation}</Cell>
//                   <Cell>{sideRecord.intensity}</Cell>
//                   <Cell>{sideRecord.fluorescence}</Cell>
//                   <Cell>
//                     <div className="flex gap-2">
//                       {sideRecord.hue > 0 && (
//                         <ChartModal
//                           data={{
//                             btnLabel: 'H',
//                             label: 'hue',
//                             values: Object.entries(sideRecord).filter(
//                               ([key, _value]) => /^h\d+$/.test(key)
//                             ) as [],
//                           }}
//                         />
//                       )}
//                       {sideRecord.saturation > 0 && (
//                         <ChartModal
//                           data={{
//                             btnLabel: 'S',
//                             label: 'saturation',
//                             values: Object.entries(sideRecord).filter(
//                               ([key, _value]) => /^s\d+$/.test(key)
//                             ) as [],
//                           }}
//                         />
//                       )}
//                       {sideRecord.intensity > 0 && (
//                         <ChartModal
//                           data={{
//                             btnLabel: 'V',
//                             label: 'intensity',
//                             values: Object.entries(sideRecord).filter(
//                               ([key, _value]) => /^v\d+$/.test(key)
//                             ) as [],
//                           }}
//                         />
//                       )}
//                       {sideRecord.fluorescence > 0 && (
//                         <ChartModal
//                           data={{
//                             btnLabel: 'F',
//                             label: 'fluorescence',
//                             values: Object.entries(sideRecord).filter(
//                               ([key, _value]) => /^f\d+$/.test(key)
//                             ) as [],
//                           }}
//                         />
//                       )}
//                     </div>
//                   </Cell>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         </div>
//       )}
//     </IndoorProjectPageLayout>
//   );
// }
