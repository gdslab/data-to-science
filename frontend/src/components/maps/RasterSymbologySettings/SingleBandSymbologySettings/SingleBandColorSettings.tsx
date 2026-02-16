import { DataProduct } from '../../../pages/workspace/projects/Project';
import RasterSymbologyFieldSet from '../RasterSymbologyFieldset';
import RasterSymbologyOpacitySlider from '../RasterSymbologyOpacitySlider';
import SingleBandColorRampSelect from './SingleBandColorRampSelect';
import SingleBandNoDataInput from './SingleBandNoDataInput';

export default function SingleBandColorSettings({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  return (
    <RasterSymbologyFieldSet title="Color Properties">
      <SingleBandColorRampSelect dataProduct={dataProduct} />
      <RasterSymbologyOpacitySlider dataProduct={dataProduct} />
      <SingleBandNoDataInput dataProduct={dataProduct} />
    </RasterSymbologyFieldSet>
  );
}
