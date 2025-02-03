import { useMemo } from 'react';
import { ResponsiveLine } from '@nivo/line';

import {
  IndoorProjectDataViz2APIResponse,
  IndoorProjectDataViz2Record,
} from './IndoorProject';

export default function IndoorProjectDataViz2Graph({
  data,
}: {
  data: IndoorProjectDataViz2APIResponse;
}) {
  const result: IndoorProjectDataViz2Record[][] = useMemo(() => {
    const groupedData = data.results.reduce((acc, item) => {
      const { treatment } = item;
      if (!acc[treatment]) {
        acc[treatment] = [];
      }
      acc[treatment].push(item);
      return acc;
    }, {});

    return Object.values(groupedData);
  }, []);

  const findTrait = (record: IndoorProjectDataViz2Record): string | undefined => {
    return Object.keys(record).find(
      (key) => !['interval_days', 'treatment'].includes(key)
    );
  };

  const trait = findTrait(result[0][0]);

  console.log(result);
  console.log(`trait: ${trait}`);

  return (
    <div className="bg-white p-4">
      {/* {result.map((group, i) => (
        <div>
          <span className="text-lg font-bold">{`Group ${i + 1}`}</span>
          <div key={i} className="flex gap-2">
            {group
              .sort((a, b) => a.interval_days - b.interval_days)
              .map((record, j) => (
                <div
                  key={j}
                  className="w-60 p-2.5 flex flex-col bg-white border-2 border-gray-300 shadow-md"
                >
                  <div className="font-semibold">{record.treatment}</div>
                  {trait && (
                    <div className="flex justify-between gap-4">
                      <span>{trait}</span>
                      <span>{record?.[trait]?.toFixed(2) || 'NA'}</span>
                    </div>
                  )}
                </div>
              ))}
          </div>
        </div>
      ))}
      <div className="flex gap-2">
        {result?.[0].map((record) => (
          <div
            key={`interval-${record.interval_days}`}
            className="w-60 p-2.5 text-center text-lg font-bold"
          >
            {record.interval_days}
          </div>
        ))}
      </div> */}
      <div className="w-full text-center font-semibold">Day Intervals</div>
      {trait && (
        <div className="h-[400px] p-4">
          <ResponsiveLine
            data={result.map((group, i) => {
              return {
                id: `Group ${i + 1}`,
                data: group
                  .sort((a, b) => a.interval_days - b.interval_days)
                  .map((record) => ({
                    x: record.interval_days,
                    y: record?.[trait]?.toFixed(2) || null,
                  })),
              };
            })}
            margin={{ top: 50, right: 110, bottom: 50, left: 60 }}
            xScale={{ type: 'point' }}
            yScale={{
              type: 'linear',
              min: 'auto',
              max: 'auto',
              // stacked: true,
              reverse: false,
            }}
            yFormat=" >-.2f"
            axisTop={null}
            axisRight={null}
            axisBottom={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: 'Dates after planting',
              legendOffset: 36,
              legendPosition: 'middle',
              truncateTickAt: 0,
            }}
            axisLeft={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: trait || 'Trait',
              legendOffset: -40,
              legendPosition: 'middle',
              truncateTickAt: 0,
            }}
            pointSize={10}
            pointColor={{ theme: 'background' }}
            pointBorderWidth={2}
            pointBorderColor={{ from: 'serieColor' }}
            pointLabel="data.yFormatted"
            pointLabelYOffset={-12}
            enableTouchCrosshair={true}
            useMesh={true}
            legends={[
              {
                anchor: 'bottom-right',
                direction: 'column',
                justify: false,
                translateX: 100,
                translateY: 0,
                itemsSpacing: 0,
                itemDirection: 'left-to-right',
                itemWidth: 80,
                itemHeight: 20,
                itemOpacity: 0.75,
                symbolSize: 12,
                symbolShape: 'circle',
                symbolBorderColor: 'rgba(0, 0, 0, .5)',
                effects: [
                  {
                    on: 'hover',
                    style: {
                      itemBackground: 'rgba(0, 0, 0, .03)',
                      itemOpacity: 1,
                    },
                  },
                ],
              },
            ]}
          />
        </div>
      )}
    </div>
  );
}
