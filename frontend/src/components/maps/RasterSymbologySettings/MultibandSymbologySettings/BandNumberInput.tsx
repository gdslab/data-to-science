import { DataProduct } from '../../../pages/workspace/projects/Project';
import {
  ColorBand,
  MultibandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';

type BandNumberProps = {
  bandColor: 'red' | 'green' | 'blue';
  dataProduct: DataProduct;
  name: keyof ColorBand;
  min: number;
  max: number;
  step: number;
};

export default function BandNumberInput({
  bandColor,
  dataProduct,
  min,
  max,
  name,
  step,
}: BandNumberProps) {
  const { state, dispatch } = useRasterSymbologyContext();
  const symbology = state[dataProduct.id].symbology as MultibandSymbology;

  const label = name === 'min' || name === 'userMin' ? 'Min' : 'Max';

  const getValue = (): number => {
    if (name === 'min' || name === 'userMin') {
      return symbology.mode === 'userDefined'
        ? symbology[bandColor].userMin
        : symbology[bandColor].min;
    } else {
      return symbology.mode === 'userDefined'
        ? symbology[bandColor].userMax
        : symbology[bandColor].max;
    }
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target
      .value as MultibandSymbology[keyof MultibandSymbology];
    const valueAsNumber = typeof value === 'string' ? parseFloat(value) : value;

    const updatedSymbology = {
      ...symbology,
      [bandColor]: { ...symbology[bandColor], [name]: valueAsNumber },
    };

    dispatch({
      type: 'SET_SYMBOLOGY',
      rasterId: dataProduct.id,
      payload: updatedSymbology,
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
        min={min}
        max={max}
        step={step}
        value={getValue()}
        disabled={symbology.mode !== 'userDefined'}
        onChange={handleInputChange}
      />
    </label>
  );
}
