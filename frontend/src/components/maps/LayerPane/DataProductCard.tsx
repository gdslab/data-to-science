import { useMapContext } from '../MapContext';

import LayerCard from './LayerCard';
import RasterStats from './RasterStats';
import RasterSymbologySettings from '../RasterSymbologySettings';
import { DataProduct } from '../../pages/projects/Project';
import { getDataProductName } from '../../pages/projects/flights/DataProducts/DataProductsTable';
import { useRasterSymbologyContext } from '../RasterSymbologyContext';

export default function DataProductCard({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { activeDataProduct, activeDataProductDispatch } = useMapContext();

  const { dispatch } = useRasterSymbologyContext();

  return (
    <LayerCard
      hover={true}
      active={
        activeDataProduct !== null && dataProduct.id === activeDataProduct.id
      }
      data-product-id={dataProduct.id}
    >
      <div className="text-slate-600 text-sm">
        <div
          className="flex flex-col gap-1.5"
          onClick={() => {
            // disable ready state for symbology while changing data products
            dispatch({
              type: 'SET_READY_STATE',
              rasterId: dataProduct.id,
              payload: false,
            });
            if (
              (dataProduct && !activeDataProduct) ||
              (dataProduct &&
                activeDataProduct &&
                dataProduct.id !== activeDataProduct.id)
            ) {
              activeDataProductDispatch({
                type: 'set',
                payload: dataProduct,
              });
            }
          }}
        >
          <div>
            <span className="font-bold">
              {getDataProductName(dataProduct.data_type)}
            </span>
          </div>
          {dataProduct.data_type !== 'point_cloud' ? (
            <fieldset className="border border-solid border-slate-300 p-2">
              <legend className="block text-sm text-gray-400 font-semibold pt-1 pb-1">
                Band Info
              </legend>
              <div className="flex flex-row flex-wrap justify-start gap-1.5">
                {dataProduct.stac_properties.eo.map((b) => {
                  return (
                    <span key={b.name} className="mr-2">
                      {b.name} ({b.description})
                    </span>
                  );
                })}
              </div>
            </fieldset>
          ) : null}
          {dataProduct.data_type !== 'point_cloud' &&
            dataProduct.stac_properties.raster.length === 1 && (
              <RasterStats
                stats={dataProduct.stac_properties.raster[0].stats}
              />
            )}
        </div>
        {activeDataProduct &&
        activeDataProduct.id === dataProduct.id &&
        dataProduct.data_type !== 'point_cloud' ? (
          <div className="mt-2">
            <RasterSymbologySettings />
          </div>
        ) : null}
      </div>
    </LayerCard>
  );
}
