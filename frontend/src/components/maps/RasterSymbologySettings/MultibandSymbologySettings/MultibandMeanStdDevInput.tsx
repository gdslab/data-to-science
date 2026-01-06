import { DataProduct } from '../../../pages/workspace/projects/Project';
import {
  MultibandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';

export default function MultibandMeanStdDevInput({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { state, dispatch } = useRasterSymbologyContext();
  const symbology = state[dataProduct.id].symbology as MultibandSymbology;

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(event.target.value);

    if (isNaN(value)) return;

    const updatedSymbology = {
      ...symbology,
      meanStdDev: value,
    };
    dispatch({
      type: 'SET_SYMBOLOGY',
      rasterId: dataProduct.id,
      payload: updatedSymbology,
    });
  };

  if (symbology.mode !== 'meanStdDev') return;

  return (
    <div className="w-1/2">
      <label className="block font-semibold pt-2 pb-1" htmlFor="meanStdDev">
        Mean +/- Std. Dev. &times;
      </label>
      <input
        className="focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-hidden border border-gray-400 rounded-sm py-1 px-4 block w-full appearance-none disabled:bg-gray-200 disabled:cursor-not-allowed"
        type="number"
        id="meanStdDev"
        name="meanStdDev"
        min={0}
        max={100}
        step={0.1}
        value={symbology.meanStdDev}
        disabled={symbology.mode !== 'meanStdDev'}
        onChange={handleInputChange}
      />
    </div>
  );
}
