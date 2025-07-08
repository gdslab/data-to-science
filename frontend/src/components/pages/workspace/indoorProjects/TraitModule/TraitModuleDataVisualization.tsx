import { useMemo, useState } from 'react';
import { ResponsiveBar } from '@nivo/bar';
import { ColorSchemeId } from '@nivo/colors/dist/types/schemes/all';

import ColorMapSelect from './ColorMapSelect';

import { IndoorProjectDataViz2APIResponse } from '../IndoorProject';

import { titleCaseConversion } from '../utils';

export default function TraitModuleDataVisualization({
  data,
}: {
  data: IndoorProjectDataViz2APIResponse;
}) {
  const [colorOption, setColorOption] = useState('greens');

  const trait = useMemo(() => {
    if (!data.results.length) return undefined;
    return Object.keys(data.results[0]).find(
      (key) => !['interval_days', 'group'].includes(key)
    );
  }, [data.results]);

  const mergedData = useMemo(() => {
    return data.results.reduce((acc, item) => {
      const { interval_days, group } = item;
      if (!acc[interval_days]) {
        acc[interval_days] = { interval_days, id: interval_days.toString() };
      }
      if (trait) {
        acc[interval_days][group] = item[trait].toFixed(2);
      } else {
        acc[interval_days][group] = null;
      }
      return acc;
    }, {} as Record<string, any>);
  }, [data.results, trait]);

  const uniqueGroups = useMemo(() => {
    return [...new Set(data.results.map((item) => item.group))];
  }, [data.results]);

  const responsiveBarData = Object.values(mergedData);

  return (
    <div className="bg-white p-4">
      {trait && (
        <div className="h-[400px] p-4">
          <ResponsiveBar
            data={responsiveBarData}
            keys={uniqueGroups}
            indexBy="interval_days"
            enableLabel={false}
            colors={{ scheme: colorOption as ColorSchemeId }}
            margin={{ top: 100, right: 110, bottom: 60, left: 100 }}
            groupMode="grouped"
            borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
            borderWidth={1}
            theme={{
              text: {
                fontSize: 16,
              },
              legends: {
                text: {
                  fontSize: 16,
                  fontFamily: 'inherit',
                  fill: '#333333',
                },
              },
              axis: {
                legend: {
                  text: {
                    fontSize: 16,
                    fontWeight: 500,
                  },
                },
                ticks: {
                  text: {
                    fontSize: 16,
                  },
                },
              },
            }}
            axisTop={null}
            axisRight={null}
            axisBottom={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: 'Dates after planting',
              legendOffset: 50,
              legendPosition: 'middle',
              truncateTickAt: 0,
            }}
            axisLeft={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: titleCaseConversion(trait || 'Trait'),
              legendOffset: -80,
              legendPosition: 'middle',
              truncateTickAt: 0,
            }}
            legends={[
              {
                dataFrom: 'keys',
                anchor: 'top-left',
                direction: 'column',
                justify: false,
                translateX: 0,
                translateY: -100,
                itemsSpacing: 6,
                itemWidth: 100,
                itemHeight: 20,
                itemDirection: 'left-to-right',
                itemOpacity: 0.85,
                symbolSize: 16,
              },
            ]}
            role="application"
            ariaLabel="Bar chart showing trait values over time"
            barAriaLabel={(e) =>
              `${e.id}: ${e.formattedValue} at ${e.indexValue} days after planting`
            }
          />
        </div>
      )}
      <div className="w-96">
        <ColorMapSelect
          colorPreviewCount={uniqueGroups.length}
          setColorOption={setColorOption}
        />
      </div>
    </div>
  );
}
