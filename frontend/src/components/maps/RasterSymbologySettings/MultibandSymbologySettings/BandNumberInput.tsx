import { useEffect, useState } from 'react';

import { DataProduct } from '../../../pages/workspace/projects/Project';
import {
  MultibandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';
import { toSymbologyInputValue } from '../../utils';

export type BandValueName = 'min' | 'max' | 'userMin' | 'userMax';

type BandNumberProps = {
  bandColor: 'red' | 'green' | 'blue';
  dataProduct: DataProduct;
  name: BandValueName;
  step: number;
};

export default function BandNumberInput({
  bandColor,
  dataProduct,
  name,
  step,
}: BandNumberProps) {
  const { state, dispatch } = useRasterSymbologyContext();
  const symbology = state[dataProduct.id].symbology as MultibandSymbology;

  const label = name === 'min' || name === 'userMin' ? 'Min' : 'Max';
  const value = symbology[bandColor][name];

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

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(event.target.value);

    const parsed = parseFloat(event.target.value);
    if (Number.isNaN(parsed)) return;

    dispatch({
      type: 'SET_SYMBOLOGY',
      rasterId: dataProduct.id,
      payload: {
        ...symbology,
        [bandColor]: { ...symbology[bandColor], [name]: parsed },
      },
    });
  };

  return (
    <label
      className="block pt-2 pb-1 text-xs font-semibold"
      htmlFor={`${bandColor}${label}`}
    >
      {label}
      <input
        className="py-1 px-4 block text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-hidden border border-gray-400 rounded-sm w-full appearance-none disabled:bg-gray-200 disabled:cursor-not-allowed"
        type="number"
        id={`${bandColor}${label}`}
        name={`${bandColor}${label}`}
        step={step}
        value={inputValue}
        disabled={symbology.mode !== 'userDefined'}
        onChange={handleInputChange}
      />
    </label>
  );
}
