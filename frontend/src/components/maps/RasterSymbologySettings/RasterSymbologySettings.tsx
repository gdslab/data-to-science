import { useEffect } from 'react';

import { useMapContext } from '../MapContext';
import { useRasterSymbologyContext } from '../RasterSymbologyContext';
import SingleBandSymbologySettings from './SingleBandSymbologySettings';
import MultiBandSymbologySettings from './MultiBandSymbologySettings';

import {
  createDefaultMultiBandSymbology,
  createDefaultSingleBandSymbology,
  isSingleBand,
} from '../utils';

export interface BandOption {
  readonly value: number;
  readonly label: string;
}

export default function RasterSymbologySettings() {
  const { activeDataProduct } = useMapContext();
  const { state, dispatch } = useRasterSymbologyContext();

  // set initial style when data product mounted
  useEffect(() => {
    if (!activeDataProduct) return;

    // data product changing - remove current symbology
    dispatch({ type: 'SET_SYMBOLOGY', rasterId: activeDataProduct.id, payload: null });

    const { stac_properties, user_style } = activeDataProduct;

    if (user_style) {
      // default opacity to 100 for older saved styles that are missing this property
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: activeDataProduct.id,
        payload: { ...user_style, opacity: user_style.opacity ?? 100 },
      });
    } else if (isSingleBand(activeDataProduct)) {
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: activeDataProduct.id,
        payload: createDefaultSingleBandSymbology(stac_properties),
      });
    } else {
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: activeDataProduct.id,
        payload: createDefaultMultiBandSymbology(stac_properties),
      });
    }

    // update ready state for symbology
    dispatch({
      type: 'SET_READY_STATE',
      rasterId: activeDataProduct.id,
      payload: true,
    });
  }, [activeDataProduct]);

  if (
    !activeDataProduct ||
    !state[activeDataProduct.id] ||
    !state[activeDataProduct.id].symbology ||
    !state[activeDataProduct.id].isLoaded
  )
    return null;

  if (isSingleBand(activeDataProduct)) {
    return <SingleBandSymbologySettings dataProduct={activeDataProduct} />;
  } else {
    return <MultiBandSymbologySettings dataProduct={activeDataProduct} />;
  }
}
