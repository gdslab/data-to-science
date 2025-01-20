import BandSettings from './BandSettings';
import { DataProduct } from '../../../pages/projects/Project';

export default function MultibandBandProperties({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  return (
    <div className="mt-4 flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-4">
        <BandSettings bandColor="red" dataProduct={dataProduct} />
        <BandSettings bandColor="green" dataProduct={dataProduct} />
        <BandSettings bandColor="blue" dataProduct={dataProduct} />
      </div>
    </div>
  );
}
