import { DataProduct } from '../../pages/projects/Project';
import OpacitySlider from '../OpacitySlider';
import {
  MultibandSymbology,
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../RasterSymbologyContext';

export default function RasterSymbologyOpacitySlider({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { state, dispatch } = useRasterSymbologyContext();

  const symbology = state[dataProduct.id].symbology;

  // Early return if symbology is null
  if (!symbology) return null;

  const isSingleBandSymbology = (
    symbology: SingleBandSymbology | MultibandSymbology
  ): symbology is SingleBandSymbology => {
    return 'colorRamp' in symbology;
  };

  const isMultibandSymbology = (
    symbology: SingleBandSymbology | MultibandSymbology
  ): symbology is MultibandSymbology => {
    return 'red' in symbology;
  };

  const handleChange = (_: Event, value: number | number[]) => {
    if (typeof value === 'number') {
      if (isSingleBandSymbology(symbology)) {
        const updatedSymbology = {
          ...symbology,
          opacity: value,
        } as SingleBandSymbology;
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: dataProduct.id,
          payload: updatedSymbology,
        });
      } else if (isMultibandSymbology(symbology)) {
        const updatedSymbology = { ...symbology, opacity: value } as MultibandSymbology;
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: dataProduct.id,
          payload: updatedSymbology,
        });
      } else {
        console.error('Unknown symbology type');
      }
    } else {
      console.error('Unexpected array value for opacity slider');
    }
  };

  return (
    <div className="mt-4">
      <OpacitySlider currentValue={symbology.opacity} onChange={handleChange} />
    </div>
  );
}
