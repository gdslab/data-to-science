import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';
import SingleBandColorSettings from './SingleBandColorSettings';
import SingleBandMinMaxSettings from './SingleBandMinMaxSettings';

export default function SingleBandSymbologySettings() {
  const { state } = useRasterSymbologyContext();

  const symbology = state.symbology as SingleBandSymbology;

  if (!symbology) return;

  return (
    <div className="mb-4">
      <SingleBandColorSettings />
      <SingleBandMinMaxSettings />
    </div>
  );
}
