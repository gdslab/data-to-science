import { useRasterSymbologyContext } from '../../RasterSymbologyContext';
import RasterSymbologyFieldSet from '../RasterSymbologyFieldset';
import RasterSymbologyModeRadioGroup from '../RasterSymbologyModeRadioGroup';
import RasterSymbologyOpacitySlider from '../RasterSymbologyOpacitySlider';
import MultiBandBandProperties from './MultiBandBandProperties';
import MultiBandMeanStdDevInput from './MultiBandMeanStdDevInput';

export default function MultiBandSymbologySettings() {
  const {
    state: { symbology },
  } = useRasterSymbologyContext();

  if (!symbology) return;

  return (
    <div className="mb-4">
      <RasterSymbologyFieldSet title="RGB Properties">
        <RasterSymbologyModeRadioGroup />
        <MultiBandMeanStdDevInput />
        <MultiBandBandProperties />
        <RasterSymbologyOpacitySlider />
      </RasterSymbologyFieldSet>
    </div>
  );
}
