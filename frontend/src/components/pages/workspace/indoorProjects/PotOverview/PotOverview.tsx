import { useMemo, useState } from 'react';
import Box from '@mui/material/Box';
import Slider from '@mui/material/Slider';

import CircleItem from './CircleItem';
import { IndoorProjectDataVizRecord } from '../IndoorProject';
import Legend from './Legend';

import { customSliderStyles } from './sliderStyles';
import { PotOverviewProps } from './types';

export default function PotOverview({
  data,
  indoorProjectDataSpreadsheet,
  indoorProjectId,
}: PotOverviewProps) {
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
  console.log(indoorProjectDataSpreadsheet);
  console.log(potsOnDayInterval);
  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <Box
        sx={{ display: 'flex', flexDirection: 'column', gap: 2, width: '100%' }}
      >
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, width: '100%' }}>
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
        </Box>
        <Box sx={{ display: 'flex', gap: 2, width: '100%' }}>
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
          <span>Days</span>
        </Box>
      </Box>
      <Box>
        <Legend />
      </Box>
    </Box>
  );
}
