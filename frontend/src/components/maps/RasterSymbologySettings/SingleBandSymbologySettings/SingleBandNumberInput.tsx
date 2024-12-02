import { useMapContext } from '../../MapContext';
import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';

export default function SingleBandNumberInput({
  name,
  disabled = false,
}: {
  name: 'min' | 'max' | 'userMin' | 'userMax' | 'meanStdDev';
  disabled?: boolean;
}) {
  const { activeDataProduct } = useMapContext();
  const { state, dispatch } = useRasterSymbologyContext();

  const symbology = state.symbology as SingleBandSymbology;

  const rasterMin = activeDataProduct?.stac_properties?.raster?.[0]?.stats.minimum;
  const rasterMax = activeDataProduct?.stac_properties?.raster?.[0]?.stats.maximum;

  // Default to 0 unless minimum raster value is negative
  const min = rasterMin && rasterMin > 0 ? 0 : rasterMin;

  // Default to maximum raster value, fallback to max value for uint8 (255)
  // Default to 100 if mean std. dev. selected as the mode
  const max = name === 'meanStdDev' ? 100 : rasterMax ? rasterMax : 255;

  const step: number =
    name === 'meanStdDev'
      ? 0.1
      : activeDataProduct?.stac_properties?.raster?.[0]?.data_type === 'uint8'
      ? 1
      : 0.001;

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const name = event.target.name as keyof SingleBandSymbology;
    const value = event.target.value as SingleBandSymbology[keyof SingleBandSymbology];

    const updatedSymbology = { ...symbology, [name]: value };

    dispatch({ type: 'SET_SYMBOLOGY', payload: updatedSymbology });
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
        className="focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none border border-gray-400 rounded py-1 px-4 block w-full appearance-none disabled:bg-gray-200 disabled:cursor-not-allowed"
        type="number"
        name={name}
        min={min}
        max={max}
        step={step}
        value={symbology[name]}
        onChange={handleInputChange}
        disabled={disabled}
      />
    </div>
  );
}
