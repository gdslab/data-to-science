import { useMemo, useState } from 'react';
import { ResponsiveLine } from '@nivo/line';
import { ColorSchemeId } from '@nivo/colors/dist/types/schemes/all';

import ColorMapSelect from './ColorMapSelect';
import {
  IndoorProjectDataViz2APIResponse,
  IndoorProjectDataViz2Record,
} from './IndoorProject';

export default function IndoorProjectDataViz2Graph({
  data,
}: {
  data: IndoorProjectDataViz2APIResponse;
}) {
  const [colorOption, setColorOption] = useState('nivo');

  const result: IndoorProjectDataViz2Record[][] = useMemo(() => {
    const groupedData = data.results.reduce((acc, item) => {
      const { group } = item;
      if (!acc[group]) {
        acc[group] = [];
      }
      acc[group].push(item);
      return acc;
    }, {});

    return Object.values(groupedData);
  }, []);

  const findTrait = (
    record: IndoorProjectDataViz2Record
  ): string | undefined => {
    return Object.keys(record).find(
      (key) => !['interval_days', 'group'].includes(key)
    );
  };

  const trait = findTrait(result[0][0]);

  return (
    <div className="bg-white p-4">
      {trait && (
        <div className="h-[400px] p-4">
          <ResponsiveLine
            data={result.map((group) => {
              return {
                id: group[0].group,
                data: group
                  .sort((a, b) => a.interval_days - b.interval_days)
                  .map((record) => ({
                    x: record.interval_days,
                    y: record?.[trait]?.toFixed(2) || null,
                  })),
              };
            })}
            colors={{ scheme: colorOption as ColorSchemeId }}
            margin={{ top: 50, right: 110, bottom: 50, left: 80 }}
            xScale={{ type: 'linear', min: 'auto', max: 'auto' }}
            yScale={{
              type: 'linear',
              min: 'auto',
              max: 'auto',
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
              legendOffset: 40,
              legendPosition: 'middle',
              truncateTickAt: 0,
            }}
            axisLeft={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: trait || 'Trait',
              legendOffset: -70,
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
      <div className="w-96">
        <ColorMapSelect setColorOption={setColorOption} />
      </div>
    </div>
  );
}
