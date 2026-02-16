import { useEffect, useState } from 'react';

import { DataProduct } from '../../../pages/workspace/projects/Project';
import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';

export default function SingleBandNoDataInput({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { state, dispatch } = useRasterSymbologyContext();
  const symbology = state[dataProduct.id].symbology as SingleBandSymbology;

  const [inputValue, setInputValue] = useState('');

  // Sync local state when symbology nodata changes externally (e.g., loading saved settings)
  useEffect(() => {
    setInputValue(
      symbology.nodata != null ? symbology.nodata.toString() : ''
    );
  }, [symbology.nodata]);

  const handleSet = () => {
    const parsed = parseFloat(inputValue);
    if (isNaN(parsed)) return;

    dispatch({
      type: 'SET_SYMBOLOGY',
      rasterId: dataProduct.id,
      payload: { ...symbology, nodata: parsed },
    });
  };

  const handleClear = () => {
    setInputValue('');
    dispatch({
      type: 'SET_SYMBOLOGY',
      rasterId: dataProduct.id,
      payload: { ...symbology, nodata: null },
    });
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSet();
    }
  };

  const currentNodata = symbology.nodata;
  const parsed = parseFloat(inputValue);
  const isSetDisabled =
    inputValue === '' || isNaN(parsed) || parsed === currentNodata;

  return (
    <div>
      <label className="block font-semibold pt-2 pb-1" htmlFor="nodata">
        No Data
      </label>
      <div className="flex items-center gap-2">
        <input
          className="focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-hidden border border-gray-400 rounded-sm py-1 px-4 block w-full appearance-none"
          type="number"
          id="nodata"
          name="nodata"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. -9999"
        />
        <button
          type="button"
          className="px-3 py-1 text-sm font-medium rounded-sm border-2 bg-accent3 hover:bg-accent3-dark border-accent3 hover:border-accent3-dark text-white ease-in-out duration-300 disabled:bg-gray-200 disabled:border-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed"
          onClick={handleSet}
          disabled={isSetDisabled}
        >
          Set
        </button>
        {currentNodata != null && (
          <button
            type="button"
            className="px-3 py-1 text-sm font-medium rounded-sm border-2 text-gray-700 bg-gray-200 hover:bg-gray-300 border-gray-300 hover:border-gray-400 ease-in-out duration-300"
            onClick={handleClear}
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}