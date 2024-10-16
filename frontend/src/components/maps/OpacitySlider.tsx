import Slider from '@mui/material/Slider';

const marks = [
  {
    value: 0,
    label: '0%',
  },
  {
    value: 25,
    label: '25%',
  },
  {
    value: 50,
    label: '50%',
  },
  {
    value: 75,
    label: '75%',
  },
  {
    value: 100,
    label: '100%',
  },
];

export default function OpacitySlider({
  currentValue,
  onChange,
}: {
  currentValue: number;
  onChange: (_: Event, newValue: number | number[]) => void;
}) {
  const getAriaValueText = (newValue: number) => `${newValue}%`;

  return (
    <div className="relative flex flex-row justify-between gap-2">
      <label className="block text-sm text-gray-400 font-bold pt-1 pb-1">Opacity</label>
      <div className="px-2 grow">
        <Slider
          aria-label="Opacity"
          defaultValue={100}
          getAriaValueText={getAriaValueText}
          step={1}
          marks={marks}
          min={0}
          max={100}
          value={currentValue}
          valueLabelDisplay="auto"
          onChange={onChange}
          sx={{
            '& .MuiSlider-thumb': {
              width: '20px',
              height: '14px',
              backgroundColor: 'white',
              border: '2px solid #ABABAB',
              borderRadius: '4px',
            },
            '& .MuiSlider-markLabel': {
              fontSize: '12px',
              fontWeight: 600,
              color: '#ABABAB',
            },
            '& .MuiSlider-mark': {
              color: '#374151',
            },
            '& .MuiSlider-valueLabel': {
              backgroundColor: 'rgba(0,0,0,0)',
              color: '#6b7280',
              fontSize: '14px',
              fontWeight: 600,
              top: '3px',
            },
            '& .MuiSlider-track': {
              height: '8px',
              color: '#3471FF',
            },
            '& .MuiSlider-rail': {
              height: '6px',
              color: '#CECECE',
            },
          }}
        />
      </div>
    </div>
  );
}
