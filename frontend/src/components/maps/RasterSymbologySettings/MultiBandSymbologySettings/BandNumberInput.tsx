import {
  ColorBand,
  MultiBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';

type BandNumberProps = {
  bandColor: 'red' | 'green' | 'blue';
  name: keyof ColorBand;
  min: number;
  max: number;
  step: number;
};

export default function BandNumberInput({
  bandColor,
  min,
  max,
  name,
  step,
}: BandNumberProps) {
  const { state, dispatch } = useRasterSymbologyContext();
  const symbology = state.symbology as MultiBandSymbology;

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
    const value = event.target.value as MultiBandSymbology[keyof MultiBandSymbology];

    const updatedSymbology = {
      ...symbology,
      [bandColor]: { [name]: value },
    };

    dispatch({ type: 'SET_SYMBOLOGY', payload: updatedSymbology });
  };

  return (
    <label
      className="block pt-2 pb-1 text-xs font-semibold"
      htmlFor={`${bandColor}${label}`}
    >
      {label}
      <input
        className="py-1 px-4 block text-xs focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none border border-gray-400 rounded w-full appearance-none disabled:bg-gray-200 disabled:cursor-not-allowed"
        type="number"
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
