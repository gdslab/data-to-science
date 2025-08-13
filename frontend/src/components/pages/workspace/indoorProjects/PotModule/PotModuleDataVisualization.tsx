import { useEffect, useMemo } from 'react';
import Slider from '@mui/material/Slider';

import CircleItem from './CircleItem';
import {
  IndoorProjectDataVizRecord,
  PotModuleDataVisualizationProps,
} from '../IndoorProject';
import { useIndoorProjectContext } from '../IndoorProjectContext';
import Legend from './Legend';
import { ShapeProvider } from './ShapeContext';

import { customSliderStyles } from './sliderStyles';
import { getNormalizedAndStretchedValues } from '../utils';

export default function PotModuleDataVisualization({
  data,
  indoorProjectDataSpreadsheet,
  indoorProjectId,
}: PotModuleDataVisualizationProps) {
  const {
    state: { selectedDAP },
    dispatch,
  } = useIndoorProjectContext();

  // Get unique treatments from spreadsheet
  const treatments = useMemo(
    () => [...new Set(indoorProjectDataSpreadsheet.summary.treatment)],
    [indoorProjectDataSpreadsheet]
  );

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

  useEffect(() => {
    dispatch({ type: 'SET_SELECTED_DAP', payload: marks[0]?.value || 0 });
  }, [marks]);

  // Format the slider value to display as days
  function valuetext(value: number) {
    return `${value} days`;
  }

  // Update state when the slider changes
  function handleOnChange(_event: Event, value: number | number[]) {
    dispatch({ type: 'SET_SELECTED_DAP', payload: value as number });
  }

  // Filter the pots on the selected day interval
  const potsOnDayInterval = result.map((group) =>
    group.filter((g) => g.interval_days === selectedDAP)
  );

  // Normalize and stretch the values for each pot across all DAPs
  const potsNormalizedAndStretchedValues = useMemo(() => {
    return result.map((p) =>
      getNormalizedAndStretchedValues(p.map((v) => [v]))
    );
  }, [result]);

  // Get the DAP intervals for the pots
  const dapIntervals = result[0].map((v) => v.interval_days);

  if (!selectedDAP) return null;

  console.log(indoorProjectDataSpreadsheet);
  console.log('group', potsOnDayInterval);

  return (
    <ShapeProvider treatments={treatments}>
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
                  saturation:
                    potsNormalizedAndStretchedValues[index].stretchedSValues[
                      dapIntervals.indexOf(selectedDAP)
                    ],
                  intensity:
                    potsNormalizedAndStretchedValues[index].stretchedVValues[
                      dapIntervals.indexOf(selectedDAP)
                    ],
                }}
              />
            ))}
          </div>
          <div className="flex gap-8 w-full">
            <Slider
              aria-label="Custom marks"
              value={selectedDAP}
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
          <Legend treatments={treatments} />
        </div>
      </div>
    </ShapeProvider>
  );
}
