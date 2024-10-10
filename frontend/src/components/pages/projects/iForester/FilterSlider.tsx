import Slider from '@mui/material/Slider';

import { getUniqueValues } from './IForesterMap';

type FilterSlider = {
  name: string;
  label: string;
  minThumb: number;
  maxThumb: number;
  unit: string;
  updateMinThumb: (value: number) => void;
  updateMaxThumb: (value: number) => void;
  values: number[];
};

export default function FilterSlider({
  name,
  label,
  minThumb,
  maxThumb,
  unit,
  updateMinThumb,
  updateMaxThumb,
  values,
}: FilterSlider) {
  function valuetext(value: number) {
    return `${value} ${unit}`;
  }

  const marks = getUniqueValues(values).map((v) => ({
    label: `${v} ${unit}`,
    value: v as number,
  }));

  const min = Math.min.apply(Math, values);
  const max = Math.max.apply(Math, values);

  return (
    <div className="flex justify-center h-52 p-2.5">
      <Slider
        id={name}
        getAriaLabel={() => label}
        orientation="vertical"
        getAriaValueText={valuetext}
        defaultValue={[minThumb, maxThumb]}
        marks={marks}
        min={min}
        max={max}
        valueLabelDisplay="on"
        value={[minThumb, maxThumb]}
        onChange={(_, newValues) => {
          updateMinThumb(newValues[0]);
          updateMaxThumb(newValues[1]);
        }}
        sx={{
          '& .MuiSlider-thumb': {
            width: '14px',
            height: '4px',
            backgroundColor: 'white',
            border: '1px solid #ABABAB',
            borderRadius: '6px',
          },
          '& .MuiSlider-markLabel': {
            fontSize: '10px',
            color: '#ABABAB',
            left: '30px',
          },
          '& .MuiSlider-valueLabel': {
            backgroundColor: 'rgba(0,0,0,0)',
            color: 'black',
            fontSize: '12px',
            right: '10px',
          },
          '& .MuiSlider-track': {
            width: '6px',
            color: '#3471FF',
          },
          '& .MuiSlider-rail': {
            width: '4px',
            color: '#CECECE',
          },
        }}
      />
    </div>
  );
}
