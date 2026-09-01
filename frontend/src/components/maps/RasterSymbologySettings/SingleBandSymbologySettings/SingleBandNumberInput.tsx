import { useEffect, useState } from 'react';

import { DataProduct } from '../../../pages/workspace/projects/Project';
import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';
import { toSymbologyInputValue } from '../../utils';

export default function SingleBandNumberInput({
  name,
  dataProduct,
  disabled = false,
}: {
  name: 'min' | 'max' | 'userMin' | 'userMax' | 'meanStdDev';
  dataProduct: DataProduct;
  disabled?: boolean;
}) {
  const { state, dispatch } = useRasterSymbologyContext();

  const symbology = state[dataProduct.id].symbology as SingleBandSymbology;

  const isMeanStdDev = name === 'meanStdDev';
  const value = symbology[name];

  const [inputValue, setInputValue] = useState(() =>
    toSymbologyInputValue(value)
  );

  // Sync when the symbology changes outside this input (mode switch, saved
  // style loaded) without disturbing partial input such as "-" or "5."
  useEffect(() => {
    setInputValue((prev) =>
      parseFloat(prev) === value ? prev : toSymbologyInputValue(value)
    );
  }, [value]);

  const step: number = isMeanStdDev
    ? 0.1
    : dataProduct.stac_properties.raster[0].data_type === 'uint8'
    ? 1
    : 0.001;

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(event.target.value);

    const parsed = parseFloat(event.target.value);
    if (Number.isNaN(parsed)) return;

    dispatch({
      type: 'SET_SYMBOLOGY',
      rasterId: dataProduct.id,
      payload: { ...symbology, [name]: parsed },
    });
  };

  const labelName = ['min', 'userMin'].includes(name)
    ? 'Min'
    : ['max', 'userMax'].includes(name)
    ? 'Max'
    : 'Mean +/- Std. Dev. × ';

  return (
    <div className="grow">
      <label className="block font-semibold pt-2 pb-1" htmlFor={name}>
        {labelName}
      </label>
      <input
        className="focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-hidden border border-gray-400 rounded-sm py-1 px-4 block w-full appearance-none disabled:bg-gray-200 disabled:cursor-not-allowed"
        type="number"
        id={name}
        name={name}
        min={isMeanStdDev ? 0 : undefined}
        max={isMeanStdDev ? 100 : undefined}
        step={step}
        value={inputValue}
        onChange={handleInputChange}
        disabled={disabled}
      />
    </div>
  );
}
