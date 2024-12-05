import { DataProduct } from '../../../pages/projects/Project';
import RasterSymbologyFieldSet from '../RasterSymbologyFieldset';
import RasterSymbologyOpacitySlider from '../RasterSymbologyOpacitySlider';
import SingleBandColorRampSelect from './SingleBandColorRampSelect';

export default function SingleBandColorSettings({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  return (
    <RasterSymbologyFieldSet title="Color Properties">
      <SingleBandColorRampSelect dataProduct={dataProduct} />
      <RasterSymbologyOpacitySlider dataProduct={dataProduct} />
    </RasterSymbologyFieldSet>
  );
}
