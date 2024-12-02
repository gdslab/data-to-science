import RasterSymbologyFieldSet from '../RasterSymbologyFieldset';
import RasterSymbologyOpacitySlider from '../RasterSymbologyOpacitySlider';
import SingleBandColorRampSelect from './SingleBandColorRampSelect';

export default function SingleBandColorSettings() {
  return (
    <RasterSymbologyFieldSet title="Color Properties">
      <SingleBandColorRampSelect />
      <RasterSymbologyOpacitySlider />
    </RasterSymbologyFieldSet>
  );
}
