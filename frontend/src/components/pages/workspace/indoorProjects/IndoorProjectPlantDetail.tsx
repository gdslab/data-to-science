import axios, { AxiosResponse, isAxiosError } from 'axios';
// import { useMemo, useState } from 'react';
import { Link, Params, useLoaderData, useParams } from 'react-router-dom';
// import { ResponsiveBar } from '@nivo/bar';

import IndoorProjectPageLayout from './IndoorProjectPageLayout';
import {
  IndoorProjectDataPlantAPIResponse,
  IndoorProjectDataVizAPIResponse,
} from './IndoorProject';
// import Modal from '../../../Modal';
import IndoorProjectDataVizGraph from './IndoorProjectDataVizGraph';

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

// const ImageModal = ({
//   filename,
//   indoorProjectId,
//   indoorProjectDataId,
// }: {
//   filename: string;
//   indoorProjectId: string;
//   indoorProjectDataId: string;
// }) => {
//   const [isOpen, setIsOpen] = useState(false);

//   const toggleIsOpen = () => setIsOpen(!isOpen);

//   const degs = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];

//   const parts = filename.split('_');

//   return (
//     <div className="relative">
//       <button onClick={toggleIsOpen}>Images</button>
//       <Modal open={isOpen} setOpen={setIsOpen}>
//         <div className="p-4 h-[400px]">
//           <h3>Images</h3>
//           <h4>RGB</h4>
//           <ul className="list-disc list-inside">
//             {degs.map((deg) => (
//               <li key={deg}>
//                 <a
//                   href={`/static/indoor_projects/${indoorProjectId}/uploaded/${indoorProjectDataId}/Saturated/${
//                     parts[0]
//                   }_R_${parts[2]}_${parts[3]}_RGB-SideFull-${deg}-PNG_${
//                     parts[5]
//                   }_${parts[6]}_${parts[7].slice(0, -4)}.png`}
//                   target="_blank"
//                 >
//                   {`${parts[0]}_R_${parts[2]}_${
//                     parts[3]
//                   }_RGB-SideFull-${deg}-PNG_${parts[5]}_${
//                     parts[6]
//                   }_${parts[7].slice(0, -4)}.png`}
//                 </a>
//               </li>
//             ))}
//           </ul>
//         </div>
//       </Modal>
//     </div>
//   );
// };

// const ChartModal = ({
//   data,
// }: {
//   data: { btnLabel: string; label: string; values: [string, number][] };
// }) => {
//   const [isOpen, setIsOpen] = useState(false);

//   const toggleIsOpen = () => setIsOpen(!isOpen);

//   return (
//     <div className="relative">
//       <button onClick={toggleIsOpen}>{data.btnLabel}</button>
//       <Modal open={isOpen} setOpen={setIsOpen}>
//         <div className="p-4 h-[400px]">
//           <ResponsiveBar
//             data={data.values.map((row, index) => ({
//               index: index + 1,
//               [data.label]: row[1],
//             }))}
//             keys={[data.label]}
//             indexBy="index"
//             margin={{ top: 50, right: 15, bottom: 50, left: 60 }}
//             padding={0.3}
//             valueScale={{ type: 'linear' }}
//             indexScale={{ type: 'band', round: true }}
//             colors={{ scheme: 'nivo' }}
//             borderColor={{
//               from: 'color',
//               modifiers: [['darker', 1.6]],
//             }}
//             axisTop={null}
//             axisRight={null}
//             axisBottom={{
//               tickSize: 5,
//               tickPadding: 5,
//               tickRotation: 0,
//               tickValues:
//                 data.values.length <= 100
//                   ? [0, 25, 50, 75, 100]
//                   : [0, 50, 100, 150, 200, 250, 300, 350],
//               legend: data.label,
//               legendPosition: 'middle',
//               legendOffset: 35,
//               truncateTickAt: 0,
//             }}
//             axisLeft={{
//               tickSize: 5,
//               tickPadding: 5,
//               tickRotation: 0,
//               legend: 'count',
//               legendPosition: 'middle',
//               legendOffset: -50,
//               truncateTickAt: 0,
//             }}
//             labelSkipWidth={12}
//             labelSkipHeight={12}
//             labelTextColor={{
//               from: 'color',
//               modifiers: [['darker', 1.6]],
//             }}
//             role="application"
//             ariaLabel={`${data.label} Bar Chart`}
//             barAriaLabel={(e) => e.id + ': ' + e.formattedValue}
//           />
//         </div>
//       </Modal>
//     </div>
//   );
// };

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

  console.log(indoorProjectPlant);

  if (
    !indoorProjectPlant.ppew ||
    !indoorProjectPlant.topChart ||
    !indoorProjectPlant.sideChart
  )
    return null;

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
          <IndoorProjectDataVizGraph data={indoorProjectPlant.topChart} />
        </div>
        {/* Side chart */}
        <div>
          <h2>Side average</h2>
          <IndoorProjectDataVizGraph data={indoorProjectPlant.sideChart} />
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
