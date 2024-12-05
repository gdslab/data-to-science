import { DataProduct } from '../../../pages/projects/Project';
import SingleBandColorSettings from './SingleBandColorSettings';
import SingleBandMinMaxSettings from './SingleBandMinMaxSettings';

export default function SingleBandSymbologySettings({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  return (
    <div className="mb-4">
      <SingleBandColorSettings dataProduct={dataProduct} />
      <SingleBandMinMaxSettings dataProduct={dataProduct} />
    </div>
  );
}
