import OpacitySlider from '../OpacitySlider';
import {
  MultiBandSymbology,
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../RasterSymbologyContext';

export default function RasterSymbologyOpacitySlider() {
  const { state, dispatch } = useRasterSymbologyContext();

  const symbology = state.symbology;

  const isSingleBandSymbology = (symbology: any): symbology is SingleBandSymbology => {
    return 'colorRamp' in symbology;
  };

  const isMultiBandSymbology = (symbology: any): symbology is MultiBandSymbology => {
    return 'red' in symbology;
  };

  const handleChange = (_: Event, value: number | number[]) => {
    if (typeof value === 'number') {
      if (isSingleBandSymbology(symbology)) {
        const updatedSymbology = {
          ...symbology,
          opacity: value,
        } as SingleBandSymbology;
        dispatch({ type: 'SET_SYMBOLOGY', payload: updatedSymbology });
      } else if (isMultiBandSymbology(symbology)) {
        const updatedSymbology = { ...symbology, opacity: value } as MultiBandSymbology;
        dispatch({ type: 'SET_SYMBOLOGY', payload: updatedSymbology });
      } else {
        console.error('Unknown symbology type');
      }
    } else {
      console.error('Unexpected array value for opacity slider');
    }
  };

  if (!symbology) return;

  return <OpacitySlider currentValue={symbology.opacity} onChange={handleChange} />;
}
