import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';
import RasterSymbologyFieldSet from '../RasterSymbologyFieldset';
import RasterSymbologyModeRadioGroup from '../RasterSymbologyModeRadioGroup';
import SingleBandNumberInput from './SingleBandNumberInput';

export default function SingleBandMinMaxSettings() {
  const { state } = useRasterSymbologyContext();
  const symbology = state.symbology as SingleBandSymbology;

  return (
    <RasterSymbologyFieldSet title="Min / Max Value Settings">
      <RasterSymbologyModeRadioGroup />
      {symbology.mode === 'minMax' && (
        <div className="flex justify-between gap-4">
          <SingleBandNumberInput name="min" disabled />
          <SingleBandNumberInput name="max" disabled />
        </div>
      )}
      {symbology.mode === 'userDefined' && (
        <div className="flex justify-between gap-4">
          <SingleBandNumberInput
            name="userMin"
            disabled={symbology.mode !== 'userDefined'}
          />
          <SingleBandNumberInput
            name="userMax"
            disabled={symbology.mode !== 'userDefined'}
          />
        </div>
      )}
      {symbology.mode === 'meanStdDev' && (
        <div className="w-1/2">
          <SingleBandNumberInput
            name="meanStdDev"
            disabled={symbology.mode !== 'meanStdDev'}
          />
        </div>
      )}
    </RasterSymbologyFieldSet>
  );
}
