import { DataProduct } from '../../../pages/projects/Project';
import RasterSymbologyFieldSet from '../RasterSymbologyFieldset';
import RasterSymbologyModeRadioGroup from '../RasterSymbologyModeRadioGroup';
import RasterSymbologyOpacitySlider from '../RasterSymbologyOpacitySlider';
import MultibandBandProperties from './MultibandBandProperties';
import MultibandMeanStdDevInput from './MultibandMeanStdDevInput';

export default function MultibandSymbologySettings({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  return (
    <div className="mb-4">
      <RasterSymbologyFieldSet title="RGB Properties">
        <RasterSymbologyModeRadioGroup dataProduct={dataProduct} />
        <MultibandMeanStdDevInput dataProduct={dataProduct} />
        <MultibandBandProperties dataProduct={dataProduct} />
        <RasterSymbologyOpacitySlider dataProduct={dataProduct} />
      </RasterSymbologyFieldSet>
    </div>
  );
}
