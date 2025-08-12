import { useMemo, useState } from 'react';
import { ResponsiveScatterPlot } from '@nivo/scatterplot';
import { ColorSchemeId } from '@nivo/colors/dist/types/schemes/all';

import ColorMapSelect from './ColorMapSelect';

import { IndoorProjectDataVizScatterAPIResponse } from '../IndoorProject';

import { titleCaseConversion, nivoCategoricalColors } from '../utils';

export default function TraitScatterModuleDataVisualization({
  data,
}: {
  data: IndoorProjectDataVizScatterAPIResponse;
}) {
  const [colorOption, setColorOption] = useState('paired');

  // Transform data for Nivo scatter plot format
  const scatterData = useMemo(() => {
    // Group data by group (treatment, etc.)
    const groupedData = data.results.reduce((acc, item) => {
      if (!acc[item.group]) {
        acc[item.group] = {
          id: item.group,
          data: [],
        };
      }
      acc[item.group].data.push({
        x: item.x,
        y: item.y,
        id: item.id,
        interval_days: item.interval_days,
      });
      return acc;
    }, {} as Record<string, any>);

    return Object.values(groupedData);
  }, [data.results]);

  const uniqueGroups = useMemo(() => {
    return [...new Set(data.results.map((item) => item.group))];
  }, [data.results]);

  // Find the 'paired' color scheme option
  const pairedColorOption = nivoCategoricalColors.find(
    (option) => option.value === 'paired'
  );

  return (
    <div className="bg-white p-4">
      {scatterData.length > 0 && (
        <div className="h-[500px] p-4">
          <ResponsiveScatterPlot
            data={scatterData}
            margin={{ top: 80, right: 140, bottom: 70, left: 90 }}
            xScale={{ type: 'linear', min: 'auto', max: 'auto' }}
            yScale={{ type: 'linear', min: 'auto', max: 'auto' }}
            colors={{ scheme: colorOption as ColorSchemeId }}
            blendMode="normal"
            axisTop={null}
            axisRight={null}
            axisBottom={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: titleCaseConversion(data.traits.x),
              legendOffset: 46,
              legendPosition: 'middle',
            }}
            axisLeft={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: titleCaseConversion(data.traits.y),
              legendOffset: -75,
              legendPosition: 'middle',
            }}
            theme={{
              text: {
                fontSize: 14,
              },
              legends: {
                text: {
                  fontSize: 14,
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
                    fontSize: 14,
                  },
                },
              },
            }}
            legends={[
              {
                anchor: 'top-left',
                direction: 'column',
                justify: false,
                translateX: 0,
                translateY: -80,
                itemWidth: 100,
                itemHeight: 12,
                itemsSpacing: 5,
                itemDirection: 'left-to-right',
                symbolSize: 12,
                symbolShape: 'circle',
                itemOpacity: 0.85,
                effects: [
                  {
                    on: 'hover',
                    style: {
                      itemOpacity: 1,
                    },
                  },
                ],
              },
            ]}
            nodeSize={8}
            animate={true}
            motionConfig="gentle"
            tooltip={({ node }) => {
              const xValue =
                typeof node.data.x === 'number'
                  ? node.data.x.toFixed(2)
                  : node.data.x;
              const yValue =
                typeof node.data.y === 'number'
                  ? node.data.y.toFixed(2)
                  : node.data.y;
              const intervalDays = (node.data as any).interval_days;

              return (
                <div
                  style={{
                    background: 'white',
                    padding: '12px 16px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}
                >
                  <strong>{node.serieId}</strong>
                  <br />
                  {titleCaseConversion(data.traits.x)}: {xValue}
                  <br />
                  {titleCaseConversion(data.traits.y)}: {yValue}
                  <br />
                  Days after planting: {intervalDays}
                </div>
              );
            }}
            role="application"
            ariaLabel="Scatter plot showing relationship between two traits"
          />
        </div>
      )}
      <div className="w-96">
        <ColorMapSelect
          colorPreviewCount={uniqueGroups.length}
          setColorOption={setColorOption}
          defaultValue={pairedColorOption}
        />
      </div>
    </div>
  );
}
