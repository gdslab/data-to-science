import clsx from 'clsx';

import BandSelect from './BandSelect';
import {
  MultibandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';
import { DataProduct } from '../../../pages/workspace/projects/Project';
import BandNumberInput, { BandValueName } from './BandNumberInput';

export interface BandOption {
  readonly value: number;
  readonly label: string;
}

type BandSettingsProps = {
  bandColor: 'red' | 'green' | 'blue';
  dataProduct: DataProduct;
};

export default function BandSettings({
  bandColor,
  dataProduct,
}: BandSettingsProps) {
  const { state } = useRasterSymbologyContext();
  const symbology = state[dataProduct.id].symbology as MultibandSymbology;

  const bandOptions: BandOption[] = dataProduct.stac_properties.eo.map(
    (band, idx) => ({
      label: band.name,
      value: idx + 1,
    })
  );

  const step: number =
    dataProduct.stac_properties.raster[0].data_type === 'uint8' ? 1 : 0.001;

  const inputNames: BandValueName[] =
    symbology.mode === 'userDefined' ? ['userMin', 'userMax'] : ['min', 'max'];

  return (
    <div
      className={clsx(
        'grid grid-rows-3 gap-1.5 p-1.5 border-2 border-dotted rounded-md',
        {
          'border-red-500': bandColor === 'red',
          'border-green-500': bandColor === 'green',
          'border-blue-500': bandColor === 'blue',
          'border-gray-500': !['red', 'green', 'blue'].includes(bandColor),
        }
      )}
    >
      <BandSelect
        bandColor={bandColor}
        dataProduct={dataProduct}
        options={bandOptions}
      />
      {inputNames.map((name) => (
        <BandNumberInput
          key={`${bandColor}-${name}`}
          bandColor={bandColor}
          dataProduct={dataProduct}
          name={name}
          step={step}
        />
      ))}
    </div>
  );
}
