import { useMemo } from 'react';
import Select, { SingleValue } from 'react-select';

import { DataProduct } from '../../../pages/projects/Project';

import { useMapContext } from '../../MapContext';

import { createDefaultSingleBandSymbology, isSingleBand } from '../../utils';
import RasterSymbologyFieldSet from '../RasterSymbologyFieldset';
import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../../RasterSymbologyContext';

interface BackgroundRasterOption {
  readonly value: string;
  readonly label: string;
}

export default function BackgroundRasterSelect({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { flights } = useMapContext();

  const { state, dispatch } = useRasterSymbologyContext();

  const backgroundRasters: DataProduct[] | undefined = useMemo(() => {
    const flight = flights.find(({ id }) => id === dataProduct.flight_id);

    return flight?.data_products.filter(
      (dp) => dp.id !== dataProduct.id && isSingleBand(dp)
    );
  }, [dataProduct, flights]);

  const backgroundRasterOptions: BackgroundRasterOption[] | undefined = useMemo(() => {
    const options =
      backgroundRasters?.map(({ data_type, id }) => ({
        label: data_type,
        value: id,
      })) || [];

    return [{ label: 'None', value: '' }, ...options];
  }, [dataProduct, flights]);

  const handleChange = (
    backgroundRasterOption: SingleValue<BackgroundRasterOption>
  ) => {
    if (backgroundRasterOption) {
      const backgroundDataProduct = backgroundRasters?.find(
        ({ id }) => id === backgroundRasterOption.value
      );
      if (backgroundDataProduct) {
        const { stac_properties, user_style } = backgroundDataProduct;

        if (user_style && !state[backgroundDataProduct.id]?.symbology) {
          // user style exists and symbology context has not yet been set
          dispatch({
            type: 'SET_SYMBOLOGY',
            rasterId: backgroundDataProduct.id,
            payload: { ...user_style, opacity: user_style.opacity ?? 100 },
          });
        } else if (state[backgroundDataProduct.id]?.symbology) {
          // symbology context exists, uses it
          dispatch({
            type: 'SET_SYMBOLOGY',
            rasterId: backgroundDataProduct.id,
            payload: state[backgroundDataProduct.id].symbology,
          });
        } else if (isSingleBand(backgroundDataProduct)) {
          // no user style and no symbology context, use default single band symbology
          dispatch({
            type: 'SET_SYMBOLOGY',
            rasterId: backgroundDataProduct.id,
            payload: createDefaultSingleBandSymbology(stac_properties),
          });
        }

        // update ready state for symbology
        dispatch({
          type: 'SET_READY_STATE',
          rasterId: backgroundDataProduct.id,
          payload: true,
        });

        // update active data product's background property
        const symbology = state[dataProduct.id].symbology as SingleBandSymbology;
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: dataProduct.id,
          payload: {
            ...symbology,
            background: backgroundDataProduct,
            opacity: 75,
          },
        });
      } else {
        const symbology = state[dataProduct.id].symbology as SingleBandSymbology;
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: dataProduct.id,
          payload: { ...symbology, background: undefined },
        });
      }
    }
  };

  if (!backgroundRasterOptions) return null;

  return (
    <RasterSymbologyFieldSet title="Background Raster">
      <Select<BackgroundRasterOption>
        styles={{
          input: (base) => ({
            ...base,
            'input:focus': {
              boxShadow: 'none',
            },
          }),
        }}
        theme={(theme) => ({
          ...theme,
          colors: {
            ...theme.colors,
            primary: '#3d5a80',
            primary25: '#e2e8f0',
          },
        })}
        isSearchable
        defaultValue={backgroundRasterOptions[0]}
        options={backgroundRasterOptions}
        onChange={handleChange}
      />
    </RasterSymbologyFieldSet>
  );
}
