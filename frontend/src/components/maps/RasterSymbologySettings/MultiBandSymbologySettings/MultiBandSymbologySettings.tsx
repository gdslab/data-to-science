import { DataProduct } from '../../../pages/projects/Project';
import RasterSymbologyFieldSet from '../RasterSymbologyFieldset';
import RasterSymbologyModeRadioGroup from '../RasterSymbologyModeRadioGroup';
import RasterSymbologyOpacitySlider from '../RasterSymbologyOpacitySlider';
import MultiBandBandProperties from './MultiBandBandProperties';
import MultiBandMeanStdDevInput from './MultiBandMeanStdDevInput';

export default function MultiBandSymbologySettings({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  return (
    <div className="mb-4">
      <RasterSymbologyFieldSet title="RGB Properties">
        <RasterSymbologyModeRadioGroup dataProduct={dataProduct} />
        <MultiBandMeanStdDevInput dataProduct={dataProduct} />
        <MultiBandBandProperties dataProduct={dataProduct} />
        <RasterSymbologyOpacitySlider dataProduct={dataProduct} />
      </RasterSymbologyFieldSet>
    </div>
  );
}
