import axios, { AxiosResponse } from 'axios';
import { useMemo, useState } from 'react';
import { Params, useLoaderData, useParams } from 'react-router-dom';
import { ResponsiveBar } from '@nivo/bar';

import IndoorProjectPageLayout from './IndoorProjectPageLayout';
import { IndoorProjectDataPlantAPIResponse } from './IndoorProject';
import Modal from '../../../Modal';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const indoorProjectPlantResponse: AxiosResponse<IndoorProjectDataPlantAPIResponse> =
      await axios.get(
        `${import.meta.env.VITE_API_V1_STR}/indoor_projects/${
          params.indoorProjectId
        }/uploaded/${params.indoorProjectDataId}/plants/${params.indoorProjectPlantId}`
      );
    if (indoorProjectPlantResponse && indoorProjectPlantResponse.status == 200) {
      const data = indoorProjectPlantResponse.data;
      if (data.ppew && data.side && data.top) return data;
      return { ppew: [], side: [], top: [] };
    } else {
      throw new Response('Indoor project plant not found', { status: 404 });
    }
  } catch (err) {
    throw new Response('Indoor project plant not found', { status: 404 });
  }
}

const ImageModal = ({
  filename,
  indoorProjectId,
  indoorProjectDataId,
}: {
  filename: string;
  indoorProjectId: string;
  indoorProjectDataId: string;
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleIsOpen = () => setIsOpen(!isOpen);

  const degs = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];

  const parts = filename.split('_');

  return (
    <div className="relative">
      <button onClick={toggleIsOpen}>Images</button>
      <Modal open={isOpen} setOpen={setIsOpen}>
        <div className="p-4 h-[400px]">
          <h3>Images</h3>
          <h4>RGB</h4>
          <ul className="list-disc list-inside">
            {degs.map((deg) => (
              <li key={deg}>
                <a
                  href={`/static/indoor_projects/${indoorProjectId}/uploaded/${indoorProjectDataId}/Saturated/${
                    parts[0]
                  }_R_${parts[2]}_${parts[3]}_RGB-SideFull-${deg}-PNG_${parts[5]}_${
                    parts[6]
                  }_${parts[7].slice(0, -4)}.png`}
                  target="_blank"
                >
                  {`${parts[0]}_R_${parts[2]}_${parts[3]}_RGB-SideFull-${deg}-PNG_${
                    parts[5]
                  }_${parts[6]}_${parts[7].slice(0, -4)}.png`}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </Modal>
    </div>
  );
};

const ChartModal = ({
  data,
}: {
  data: { btnLabel: string; label: string; values: [string, number][] };
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleIsOpen = () => setIsOpen(!isOpen);

  return (
    <div className="relative">
      <button onClick={toggleIsOpen}>{data.btnLabel}</button>
      <Modal open={isOpen} setOpen={setIsOpen}>
        <div className="p-4 h-[400px]">
          <ResponsiveBar
            data={data.values.map((row, index) => ({
              index: index + 1,
              [data.label]: row[1],
            }))}
            keys={[data.label]}
            indexBy="index"
            margin={{ top: 50, right: 15, bottom: 50, left: 60 }}
            padding={0.3}
            valueScale={{ type: 'linear' }}
            indexScale={{ type: 'band', round: true }}
            colors={{ scheme: 'nivo' }}
            borderColor={{
              from: 'color',
              modifiers: [['darker', 1.6]],
            }}
            axisTop={null}
            axisRight={null}
            axisBottom={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              tickValues:
                data.values.length <= 100
                  ? [0, 25, 50, 75, 100]
                  : [0, 50, 100, 150, 200, 250, 300, 350],
              legend: data.label,
              legendPosition: 'middle',
              legendOffset: 35,
              truncateTickAt: 0,
            }}
            axisLeft={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: 'count',
              legendPosition: 'middle',
              legendOffset: -50,
              truncateTickAt: 0,
            }}
            labelSkipWidth={12}
            labelSkipHeight={12}
            labelTextColor={{
              from: 'color',
              modifiers: [['darker', 1.6]],
            }}
            role="application"
            ariaLabel={`${data.label} Bar Chart`}
            barAriaLabel={(e) => e.id + ': ' + e.formattedValue}
          />
        </div>
      </Modal>
    </div>
  );
};

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

export default function IndoorProjectDetail() {
  const { indoorProjectId, indoorProjectDataId } = useParams();

  const indoorProjectPlant = useLoaderData() as IndoorProjectDataPlantAPIResponse;

  const sortedTopData = useMemo(() => {
    if (indoorProjectPlant.top.length > 0) {
      const sorted = indoorProjectPlant.top.sort((a, b) => {
        const scanDateA = new Date(a.scan_date).getTime();
        const scanDateB = new Date(b.scan_date).getTime();

        return scanDateA - scanDateB;
      });

      return sorted;
    } else {
      return [];
    }
  }, [indoorProjectPlant.top]);

  const sortedSideData = useMemo(() => {
    if (indoorProjectPlant.side.length > 0) {
      const sorted = indoorProjectPlant.side.sort((a, b) => {
        const scanDateA = new Date(a.scan_date);
        const scanDateB = new Date(b.scan_date);

        if (scanDateA < scanDateB) return -1;
        if (scanDateA > scanDateB) return 1;

        // if scan dates are the same, sort by frame_nr
        return a.frame_nr - b.frame_nr;
      });

      return sorted;
    } else {
      return [];
    }
  }, [indoorProjectPlant.side]);

  console.log(indoorProjectPlant);

  return (
    <IndoorProjectPageLayout>
      <h1>Plant Details</h1>
      <pre className="whitespace-pre-wrap p-10 border-2 border-slate-600">
        {JSON.stringify(indoorProjectPlant.ppew, null, 2)}
      </pre>

      <h2>Top</h2>
      {sortedTopData.length > 0 && (
        <div className="max-w-full overflow-x-auto">
          <table className="min-w-[600px] w-full border-separate border-spacing-y-1 border-spacing-x-1">
            <thead>
              <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
                <HeaderCell>Filename</HeaderCell>
                <HeaderCell>Exp ID</HeaderCell>
                <HeaderCell>Pot Barcode</HeaderCell>
                <HeaderCell>Variety</HeaderCell>
                <HeaderCell>Treatment</HeaderCell>
                <HeaderCell>Scan Time</HeaderCell>
                <HeaderCell>Scan Date</HeaderCell>
                <HeaderCell>DFP</HeaderCell>
                <HeaderCell>Angle</HeaderCell>
                <HeaderCell>Surface</HeaderCell>
                <HeaderCell>Convex Hull</HeaderCell>
                <HeaderCell>Roundness</HeaderCell>
                <HeaderCell>Center of mass distance</HeaderCell>
                <HeaderCell>Center of mass x</HeaderCell>
                <HeaderCell>Center of mass y</HeaderCell>
                <HeaderCell>Hue</HeaderCell>
                <HeaderCell>Saturation</HeaderCell>
                <HeaderCell>Intensity</HeaderCell>
                <HeaderCell>Fluorescence</HeaderCell>
                <HeaderCell>Charts</HeaderCell>
              </tr>
            </thead>
            <tbody>
              {sortedTopData.map((topRecord, index) => (
                <tr key={index}>
                  <Cell extraStyles="max-w-60 truncate">
                    <span title={topRecord.filename}>{topRecord.filename}</span>
                  </Cell>
                  <Cell>{topRecord.exp_id}</Cell>
                  <Cell>{topRecord.pot_barcode}</Cell>
                  <Cell>{topRecord.variety}</Cell>
                  <Cell>{topRecord.treatment}</Cell>
                  <Cell>{topRecord.scan_time}</Cell>
                  <Cell>{topRecord.scan_date}</Cell>
                  <Cell>{topRecord.dfp}</Cell>
                  <Cell>{topRecord.angle}</Cell>
                  <Cell>{topRecord.surface}</Cell>
                  <Cell>{topRecord.convex_hull}</Cell>
                  <Cell>{topRecord.roundness}</Cell>
                  <Cell>{topRecord.center_of_mass_distance}</Cell>
                  <Cell>{topRecord.center_of_mass_x}</Cell>
                  <Cell>{topRecord.center_of_mass_y}</Cell>
                  <Cell>{topRecord.hue}</Cell>
                  <Cell>{topRecord.saturation}</Cell>
                  <Cell>{topRecord.intensity}</Cell>
                  <Cell>{topRecord.fluorescence}</Cell>
                  <Cell>
                    <div className="flex gap-2">
                      {topRecord.hue > 0 && (
                        <ChartModal
                          data={{
                            btnLabel: 'H',
                            label: 'hue',
                            values: Object.entries(topRecord).filter(([key, _value]) =>
                              /^h\d+$/.test(key)
                            ) as [],
                          }}
                        />
                      )}
                      {topRecord.saturation > 0 && (
                        <ChartModal
                          data={{
                            btnLabel: 'S',
                            label: 'saturation',
                            values: Object.entries(topRecord).filter(([key, _value]) =>
                              /^s\d+$/.test(key)
                            ) as [],
                          }}
                        />
                      )}
                      {topRecord.intensity > 0 && (
                        <ChartModal
                          data={{
                            btnLabel: 'V',
                            label: 'intensity',
                            values: Object.entries(topRecord).filter(([key, _value]) =>
                              /^v\d+$/.test(key)
                            ) as [],
                          }}
                        />
                      )}
                      {topRecord.fluorescence > 0 && (
                        <ChartModal
                          data={{
                            btnLabel: 'F',
                            label: 'fluorescence',
                            values: Object.entries(topRecord).filter(([key, _value]) =>
                              /^f\d+$/.test(key)
                            ) as [],
                          }}
                        />
                      )}
                    </div>
                  </Cell>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <h2>Side All</h2>
      {sortedSideData.length > 0 && (
        <div className="max-w-full overflow-x-auto">
          <table className="min-w-[600px] w-full border-separate border-spacing-y-1 border-spacing-x-1">
            <thead>
              <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
                <HeaderCell>Filename</HeaderCell>
                <HeaderCell>Exp ID</HeaderCell>
                <HeaderCell>Pot Barcode</HeaderCell>
                <HeaderCell>Variety</HeaderCell>
                <HeaderCell>Treatment</HeaderCell>
                <HeaderCell>Scan Time</HeaderCell>
                <HeaderCell>Scan Date</HeaderCell>
                <HeaderCell>DFP</HeaderCell>
                <HeaderCell>View</HeaderCell>
                <HeaderCell>Frame NR</HeaderCell>
                <HeaderCell>Width</HeaderCell>
                <HeaderCell>Height</HeaderCell>
                <HeaderCell>Surface</HeaderCell>
                <HeaderCell>Convex Hull</HeaderCell>
                <HeaderCell>Roundness</HeaderCell>
                <HeaderCell>Center of mass distance</HeaderCell>
                <HeaderCell>Center of mass x</HeaderCell>
                <HeaderCell>Center of mass y</HeaderCell>
                <HeaderCell>Hue</HeaderCell>
                <HeaderCell>Saturation</HeaderCell>
                <HeaderCell>Intensity</HeaderCell>
                <HeaderCell>Fluorescence</HeaderCell>
                <HeaderCell>Images</HeaderCell>
              </tr>
            </thead>
            <tbody>
              {sortedSideData.map((sideRecord, index) => (
                <tr key={index}>
                  <Cell extraStyles="max-w-60 truncate">
                    <span title={sideRecord.filename}>{sideRecord.filename}</span>
                  </Cell>
                  <Cell>{sideRecord.exp_id}</Cell>
                  <Cell>{sideRecord.pot_barcode}</Cell>
                  <Cell>{sideRecord.variety}</Cell>
                  <Cell>{sideRecord.treatment}</Cell>
                  <Cell>{sideRecord.scan_time}</Cell>
                  <Cell>{sideRecord.scan_date}</Cell>
                  <Cell>{sideRecord.dfp}</Cell>
                  <Cell>{sideRecord.view}</Cell>
                  <Cell>{sideRecord.frame_nr}</Cell>
                  <Cell>{sideRecord.width}</Cell>
                  <Cell>{sideRecord.height}</Cell>
                  <Cell>{sideRecord.surface}</Cell>
                  <Cell>{sideRecord.convex_hull}</Cell>
                  <Cell>{sideRecord.roundness}</Cell>
                  <Cell>{sideRecord.center_of_mass_distance}</Cell>
                  <Cell>{sideRecord.center_of_mass_x}</Cell>
                  <Cell>{sideRecord.center_of_mass_y}</Cell>
                  <Cell>{sideRecord.hue}</Cell>
                  <Cell>{sideRecord.saturation}</Cell>
                  <Cell>{sideRecord.intensity}</Cell>
                  <Cell>{sideRecord.fluorescence}</Cell>
                  <Cell>
                    {indoorProjectId && indoorProjectDataId && (
                      <ImageModal
                        filename={sideRecord.filename}
                        indoorProjectId={indoorProjectId}
                        indoorProjectDataId={indoorProjectDataId}
                      />
                    )}
                  </Cell>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </IndoorProjectPageLayout>
  );
}
