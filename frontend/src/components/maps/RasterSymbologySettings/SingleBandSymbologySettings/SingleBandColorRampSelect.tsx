import Select, { SingleValue } from 'react-select';

import { colorMapGroupedOptions, ColorMapOption, miscOptions } from '../cmaps';
import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';
import { DataProduct } from '../../../pages/workspace/projects/Project';

export default function SingleBandColorRampSelect({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { state, dispatch } = useRasterSymbologyContext();

  const symbology = state[dataProduct.id].symbology as SingleBandSymbology;

  // Find the matching color option from the grouped options
  const findMatchingColorOption = (
    colorRamp: string
  ): ColorMapOption | undefined => {
    for (const group of colorMapGroupedOptions) {
      const match = group.options.find((option) => option.value === colorRamp);
      if (match) return match;
    }
    return undefined;
  };

  const handleChange = (colorOption: SingleValue<ColorMapOption>) => {
    if (colorOption) {
      const updatedSymbology = {
        ...symbology,
        colorRamp: colorOption.value,
      } as SingleBandSymbology;
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: dataProduct.id,
        payload: updatedSymbology,
      });
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
      defaultValue={
        symbology.colorRamp
          ? findMatchingColorOption(symbology.colorRamp)
          : miscOptions[12]
      }
      options={colorMapGroupedOptions}
      onChange={handleChange}
    />
  );
}
