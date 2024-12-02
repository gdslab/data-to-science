import Select, { SingleValue } from 'react-select';

import { colorMapGroupedOptions, ColorMapOption, miscOptions } from '../cmaps';
import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';

export default function SingleBandColorRampSelect() {
  const { state, dispatch } = useRasterSymbologyContext();

  const symbology = state.symbology as SingleBandSymbology;

  const handleChange = (colorOption: SingleValue<ColorMapOption>) => {
    if (colorOption) {
      const updatedSymbology = {
        ...symbology,
        colorRamp: colorOption.value,
      } as SingleBandSymbology;
      dispatch({ type: 'SET_SYMBOLOGY', payload: updatedSymbology });
    }
  };

  return (
    <Select<ColorMapOption>
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
      isSearchable
      defaultValue={miscOptions[12]}
      options={colorMapGroupedOptions}
      onChange={handleChange}
    />
  );
}
