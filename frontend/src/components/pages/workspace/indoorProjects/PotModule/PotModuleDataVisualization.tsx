import { useMemo, useState } from 'react';
import Slider from '@mui/material/Slider';

import CircleItem from './CircleItem';
import {
  IndoorProjectDataVizRecord,
  PotModuleDataVisualizationProps,
} from '../IndoorProject';
import Legend from './Legend';

import { customSliderStyles } from './sliderStyles';

export default function PotModuleDataVisualization({
  data,
  indoorProjectDataSpreadsheet,
  indoorProjectId,
}: PotModuleDataVisualizationProps) {
  // Memoize the grouped data
  const result: IndoorProjectDataVizRecord[][] = useMemo(() => {
    const groupedData = data.results.reduce((acc, item) => {
      const { group } = item;
      if (!acc[group]) {
        acc[group] = [];
      }
      acc[group].push(item);
      return acc;
    }, {});
    return Object.values(groupedData);
  }, [data.results]);

  // Memoize the marks array
  const marks = useMemo(
    () =>
      result[0].map((group) => ({
        value: group.interval_days,
        label: `${group.interval_days}`,
      })),
    [result]
  );

  // Initialize the slider state with the first mark's value
  const [selectedDayInterval, setSelectedDayInterval] = useState<number>(
    marks[0]?.value || 0
  );

  // Format the slider value to display as days
  function valuetext(value: number) {
    return `${value} days`;
  }

  // Update state when the slider changes
  function handleOnChange(_event: Event, value: number | number[]) {
    setSelectedDayInterval(value as number);
  }

  // Filter the pots on the selected day interval
  const potsOnDayInterval = result.map((group) =>
    group.filter((g) => g.interval_days === selectedDayInterval)
  );

  return (
    <div className="flex gap-4 p-4">
      <div className="flex flex-col gap-4 w-full">
        <div className="flex flex-wrap gap-4 w-full">
          {potsOnDayInterval.map((group, index) => (
            <CircleItem
              key={index}
              url={`/indoor_projects/${indoorProjectId}/uploaded/${indoorProjectDataSpreadsheet.summary.id}/plants/${group[0].group}`}
              group={group[0]}
              treatment={
                indoorProjectDataSpreadsheet.records[group[0].group].treatment
              }
              hsvColor={{
                hue: group[0].hue || 0,
                saturation: group[0].saturation || 0,
                intensity: group[0].intensity || 0,
              }}
            />
          ))}
        </div>
        <div className="flex gap-8 w-full">
          <Slider
            aria-label="Custom marks"
            value={selectedDayInterval}
            getAriaValueText={valuetext}
            step={null}
            marks={marks}
            min={marks[0]?.value}
            max={marks[marks.length - 1]?.value}
            onChange={handleOnChange}
            sx={customSliderStyles}
          />
          <span className="min-w-40">Days after planting</span>
        </div>
      </div>
      <div>
        <Legend />
      </div>
    </div>
  );
}
