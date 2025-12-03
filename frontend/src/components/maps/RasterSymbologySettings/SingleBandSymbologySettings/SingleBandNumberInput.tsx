import { DataProduct } from '../../../pages/projects/Project';
import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';

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

  const rasterMin = dataProduct.stac_properties.raster[0].stats.minimum;
  const rasterMax = dataProduct.stac_properties.raster[0].stats.maximum;

  // Default to 0 unless minimum raster value is negative
  const min = rasterMin && rasterMin > 0 ? 0 : rasterMin;

  // Default to maximum raster value, fallback to max value for uint8 (255)
  // Default to 100 if mean std. dev. selected as the mode
  const max = name === 'meanStdDev' ? 100 : rasterMax ? rasterMax : 255;

  const step: number =
    name === 'meanStdDev'
      ? 0.1
      : dataProduct.stac_properties.raster[0].data_type === 'uint8'
      ? 1
      : 0.001;

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const name = event.target.name as keyof SingleBandSymbology;
    const value = event.target.value as SingleBandSymbology[keyof SingleBandSymbology];
    const valueAsNumber = typeof value === 'string' ? parseFloat(value) : value;

    const updatedSymbology = { ...symbology, [name]: valueAsNumber };

    dispatch({
      type: 'SET_SYMBOLOGY',
      rasterId: dataProduct.id,
      payload: updatedSymbology,
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
