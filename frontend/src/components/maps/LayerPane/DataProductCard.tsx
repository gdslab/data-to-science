import { useMapContext } from '../MapContext';

import LayerCard from './LayerCard';
import RasterStats from './RasterStats';
import RasterSymbologySettings from '../RasterSymbologySettings';
import { DataProduct } from '../../pages/workspace/projects/Project';
import { getDataProductName } from '../../pages/workspace/projects/flights/DataProducts/DataProductsTable';
import { useRasterSymbologyContext } from '../RasterSymbologyContext';
import { NON_MAP_DATA_TYPES } from './utils';
import { PointCloudViewer } from '../Maps';

export default function DataProductCard({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const {
    activeDataProduct,
    activeDataProductDispatch,
    pointCloudViewerDispatch,
  } = useMapContext();

  const { dispatch } = useRasterSymbologyContext();

  const isRasterType = !(NON_MAP_DATA_TYPES as readonly string[]).includes(
    dataProduct.data_type
  );
  const isPointCloud = dataProduct.data_type === 'point_cloud';

  const activateDataProduct = () => {
    dispatch({ type: 'SET_READY_STATE', rasterId: dataProduct.id, payload: false });
    if (!activeDataProduct || dataProduct.id !== activeDataProduct.id) {
      activeDataProductDispatch({ type: 'set', payload: dataProduct });
    }
  };

  const handleViewerSelect = (viewer: PointCloudViewer) => {
    activateDataProduct();
    pointCloudViewerDispatch({ type: 'set', payload: viewer });
  };

  return (
    <LayerCard
      hover={true}
      active={
        activeDataProduct !== null && dataProduct.id === activeDataProduct.id
      }
      data-product-id={dataProduct.id}
    >
      <div className="text-slate-600 text-sm">
        {isPointCloud ? (
          <div className="flex flex-col gap-2">
            <div>
              <span className="font-bold">
                {getDataProductName(dataProduct.data_type)}
              </span>
            </div>
            <div className="flex flex-col gap-1.5">
              <button
                type="button"
                className="w-full rounded border border-slate-300 px-2 py-1.5 text-left hover:bg-slate-100"
                onClick={() => handleViewerSelect('potree')}
              >
                <div className="text-xs font-semibold">View in Potree</div>
                <div className="text-xs text-slate-500">
                  Full-featured 3D viewer with measurement tools, cross-sections,
                  and classification filtering
                </div>
              </button>
              <button
                type="button"
                className="w-full rounded border border-slate-300 px-2 py-1.5 text-left hover:bg-slate-100"
                onClick={() => handleViewerSelect('map')}
              >
                <div className="text-xs font-semibold">View on map</div>
                <div className="text-xs text-slate-500">
                  Overlay the point cloud on the map alongside other data layers
                </div>
              </button>
            </div>
          </div>
        ) : (
          <div
            className="flex flex-col gap-1.5"
            onClick={() => {
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
            {isRasterType &&
              dataProduct.resolution &&
              dataProduct.resolution.unit !== 'unknown' &&
              dataProduct.crs && (
                <div className="text-xs text-slate-500">
                  Resolution: {parseFloat(dataProduct.resolution.x.toFixed(3))}{' '}
                  x {parseFloat(dataProduct.resolution.y.toFixed(3))}{' '}
                  {dataProduct.resolution.unit} (EPSG:{dataProduct.crs.epsg})
                </div>
              )}
            {isRasterType && (
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
            )}
            {isRasterType &&
              dataProduct.stac_properties.raster.length === 1 && (
                <RasterStats
                  stats={dataProduct.stac_properties.raster[0].stats}
                />
              )}
          </div>
        )}
        {activeDataProduct &&
          activeDataProduct.id === dataProduct.id &&
          isRasterType && (
            <div className="mt-2">
              <RasterSymbologySettings />
            </div>
          )}
      </div>
    </LayerCard>
  );
}
