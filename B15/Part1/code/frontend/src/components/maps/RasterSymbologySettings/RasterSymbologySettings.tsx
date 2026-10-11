import { useEffect, useRef } from 'react';

import { useMapContext } from '../MapContext';
import { useRasterSymbologyContext } from '../RasterSymbologyContext';
import SingleBandSymbologySettings from './SingleBandSymbologySettings';
import MultibandSymbologySettings from './MultibandSymbologySettings';

import {
  createDefaultMultibandSymbology,
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

  // Store state in ref to access without triggering effect
  const stateRef = useRef(state);
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  // set initial style when data product mounted
  useEffect(() => {
    if (!activeDataProduct) return;

    // data product changing - remove current symbology
    dispatch({
      type: 'SET_SYMBOLOGY',
      rasterId: activeDataProduct.id,
      payload: null,
    });

    const { stac_properties, user_style } = activeDataProduct;

    if (user_style && !stateRef.current[activeDataProduct.id]?.symbology) {
      // user style exists and symbology context has not yet been set
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: activeDataProduct.id,
        payload: { ...user_style, opacity: user_style.opacity ?? 100 },
      });
    } else if (stateRef.current[activeDataProduct.id]?.symbology) {
      // symbology context exists, uses it
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: activeDataProduct.id,
        payload: stateRef.current[activeDataProduct.id].symbology,
      });
    } else if (isSingleBand(activeDataProduct)) {
      // no user style and no symbology context, use default single band symbology
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: activeDataProduct.id,
        payload: createDefaultSingleBandSymbology(stac_properties),
      });
    } else {
      // no user style and no symbology context, use default multi band symbology
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: activeDataProduct.id,
        payload: createDefaultMultibandSymbology(stac_properties),
      });
    }

    // update ready state for symbology
    dispatch({
      type: 'SET_READY_STATE',
      rasterId: activeDataProduct.id,
      payload: true,
    });
  }, [activeDataProduct, dispatch]);

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
    return <MultibandSymbologySettings dataProduct={activeDataProduct} />;
  }
}
