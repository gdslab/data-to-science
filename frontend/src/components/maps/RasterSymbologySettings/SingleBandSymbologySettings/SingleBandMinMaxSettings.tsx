import { DataProduct } from '../../../pages/workspace/projects/Project';
import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';
import RasterSymbologyFieldSet from '../RasterSymbologyFieldset';
import RasterSymbologyModeRadioGroup from '../RasterSymbologyModeRadioGroup';
import SingleBandNumberInput from './SingleBandNumberInput';

export default function SingleBandMinMaxSettings({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { state } = useRasterSymbologyContext();
  const symbology = state[dataProduct.id].symbology as SingleBandSymbology;

  return (
    <RasterSymbologyFieldSet title="Min / Max Value Settings">
      <RasterSymbologyModeRadioGroup dataProduct={dataProduct} />
      {symbology.mode === 'minMax' && (
        <div className="flex justify-between gap-4">
          <SingleBandNumberInput
            name="min"
            dataProduct={dataProduct}
            disabled
          />
          <SingleBandNumberInput
            name="max"
            dataProduct={dataProduct}
            disabled
          />
        </div>
      )}
      {symbology.mode === 'userDefined' && (
        <div className="flex justify-between gap-4">
          <SingleBandNumberInput
            name="userMin"
            dataProduct={dataProduct}
            disabled={symbology.mode !== 'userDefined'}
          />
          <SingleBandNumberInput
            name="userMax"
            dataProduct={dataProduct}
            disabled={symbology.mode !== 'userDefined'}
          />
        </div>
      )}
      {symbology.mode === 'meanStdDev' && (
        <div className="w-1/2">
          <SingleBandNumberInput
            name="meanStdDev"
            dataProduct={dataProduct}
            disabled={symbology.mode !== 'meanStdDev'}
          />
        </div>
      )}
    </RasterSymbologyFieldSet>
  );
}
