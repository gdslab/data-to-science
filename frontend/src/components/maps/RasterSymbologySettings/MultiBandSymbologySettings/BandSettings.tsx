import clsx from 'clsx';

import BandSelect from './BandSelect';

import {
  ColorBand,
  MultiBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';
import { DataProduct } from '../../../pages/projects/Project';
import BandNumberInput from './BandNumberInput';

export interface BandOption {
  readonly value: number;
  readonly label: string;
}

type BandSettingsProps = {
  bandColor: 'red' | 'green' | 'blue';
  dataProduct: DataProduct;
};

export default function BandSettings({ bandColor, dataProduct }: BandSettingsProps) {
  const { state } = useRasterSymbologyContext();
  const symbology = state.symbology as MultiBandSymbology;

  const bandOptions: BandOption[] = dataProduct.stac_properties.eo.map((band, idx) => ({
    label: band.name,
    value: idx + 1,
  }));

  const step: number =
    dataProduct.stac_properties.raster[0].data_type == 'unit8' ? 1 : 0.001;

  const getBandStatistic = (bandIdx: number, stat: 'minimum' | 'maximum'): number => {
    if (dataProduct.stac_properties.raster.length > bandIdx - 1) {
      return dataProduct.stac_properties.raster[bandIdx - 1][stat];
    } else {
      console.warn('Unable to find band statistic, falling back to default value.');
      return stat === 'minimum' ? 0 : 255;
    }
  };

  const inputNames: Array<keyof ColorBand> =
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
      <BandSelect bandColor={bandColor} options={bandOptions} />
      {inputNames.map((name) => (
        <BandNumberInput
          key={`${bandColor}-${name}`}
          bandColor={bandColor}
          name={name}
          min={0}
          max={getBandStatistic(
            symbology[bandColor].idx,
            name === 'min' || name === 'userMin' ? 'minimum' : 'maximum'
          )}
          step={step}
        />
      ))}
    </div>
  );
}
