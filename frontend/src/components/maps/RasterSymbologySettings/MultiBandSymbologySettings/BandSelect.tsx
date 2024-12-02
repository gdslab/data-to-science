import Select from 'react-select';

import { BandOption } from '../RasterSymbologySettings';
import {
  ColorBand,
  MultiBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';

export default function BandSelect({
  bandColor,
  options,
}: {
  bandColor: 'red' | 'green' | 'blue';
  options: BandOption[];
}) {
  const { state, dispatch } = useRasterSymbologyContext();
  const symbology = state.symbology as MultiBandSymbology;

  const toNumber = (bandValue: number | string): number => {
    if (typeof bandValue === 'number') return bandValue;

    const valueAsInt = parseInt(bandValue) as ColorBand[keyof ColorBand];
    if (isNaN(valueAsInt)) {
      throw new Error(`Invalid band index value: ${bandValue}`);
    }
    return valueAsInt;
  };

  const handleBandInputChange = (
    bandColor: 'red' | 'green' | 'blue',
    value: number
  ) => {
    const updatedSymbology = {
      ...symbology,
      [bandColor]: { ...symbology[bandColor], idx: value },
    };
    dispatch({ type: 'SET_SYMBOLOGY', payload: updatedSymbology });
  };

  return (
    <label
      className="block pt-2 pb-1 text-xs font-semibold"
      htmlFor={`${bandColor}IndexSelect`}
    >
      {`${bandColor.charAt(0).toUpperCase() + bandColor.slice(1)} Band`}
      <Select<BandOption>
        name={`${bandColor}IndexSelect`}
        styles={{
          input: (base) => ({
            ...base,
            'input:focus': {
              boxShadow: 'none',
            },
          }),
        }}
        theme={(theme) => ({
          ...theme,
          colors: {
            ...theme.colors,
            primary: '#3d5a80',
            primary25: '#e2e8f0',
          },
        })}
        defaultValue={options[symbology[bandColor].idx - 1]}
        options={options}
        onChange={(bandOption) =>
          bandOption && handleBandInputChange(bandColor, toNumber(bandOption.value))
        }
      />
    </label>
  );
}
