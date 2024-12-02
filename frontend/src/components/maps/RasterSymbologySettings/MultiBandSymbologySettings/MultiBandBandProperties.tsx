import { useMapContext } from '../../MapContext';
import BandSettings from './BandSettings';

export default function MultiBandBandProperties() {
  const { activeDataProduct } = useMapContext();

  if (!activeDataProduct) return;
  return (
    <div className="mt-4 flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-4">
        <BandSettings bandColor="red" dataProduct={activeDataProduct} />
        <BandSettings bandColor="green" dataProduct={activeDataProduct} />
        <BandSettings bandColor="blue" dataProduct={activeDataProduct} />
      </div>
    </div>
  );
}
