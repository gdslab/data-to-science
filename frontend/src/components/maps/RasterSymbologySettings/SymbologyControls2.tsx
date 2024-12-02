import { useEffect } from 'react';

import { useMapContext } from '../MapContext';
import { useRasterSymbologyContext } from '../RasterSymbologyContext';
import SingleBandSymbologySettings from './SingleBandSymbologySettings';
import MultiBandSymbologySettings from './MultiBandSymbologySettings';

import {
  createDefaultDsmSymbology,
  createDefaultOrthoSymbology,
  isSingleBand,
} from '../utils';

export interface BandOption {
  readonly value: number;
  readonly label: string;
}

export default function SymbologyControls2() {
  const { activeDataProduct } = useMapContext();
  const { dispatch } = useRasterSymbologyContext();

  // set initial style when data product mounted
  useEffect(() => {
    if (!activeDataProduct) return;

    const { stac_properties, user_style } = activeDataProduct;

    if (user_style) {
      // default opacity to 100 for older saved styles that are missing this property
      dispatch({
        type: 'SET_SYMBOLOGY',
        payload: { ...user_style, opacity: user_style.opacity ?? 100 },
      });
    } else if (isSingleBand(activeDataProduct)) {
      dispatch({
        type: 'SET_SYMBOLOGY',
        payload: createDefaultDsmSymbology(stac_properties),
      });
    } else {
      dispatch({
        type: 'SET_SYMBOLOGY',
        payload: createDefaultOrthoSymbology(stac_properties),
      });
    }
  }, [activeDataProduct]);

  if (!activeDataProduct) return null;

  if (isSingleBand(activeDataProduct)) {
    return <SingleBandSymbologySettings />;
  } else {
    return <MultiBandSymbologySettings />;
  }
}
