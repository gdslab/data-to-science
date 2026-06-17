import { useState } from 'react';

import { useMapContext } from '../MapContext';
import { useMobileView } from '../MobileViewContext';

import LayerCard from './LayerCard';
import Modal from '../../Modal';
import RasterStats from './RasterStats';
import RasterSymbologySettings from '../RasterSymbologySettings';
import RasterSymbologyAccessControls from '../RasterSymbologySettings/RasterSymbologyAccessControls';
import { Button } from '../../Buttons';
import { DataProduct } from '../../pages/workspace/projects/Project';
import { getDataProductName, getDataProductTitle } from '../../pages/workspace/projects/flights/DataProducts/DataProductsTable';
import { useRasterSymbologyContext } from '../RasterSymbologyContext';
import { NON_MAP_DATA_TYPES } from './utils';
import { PointCloudViewer } from '../Maps';
import EngagementInline from '../../Engagement/EngagementInline';
import { useDataProductLike } from '../../Engagement/useDataProductLike';

export default function DataProductCard({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const {
    activeDataProduct,
    activeDataProductDispatch,
    activeProject,
    pointCloudViewerDispatch,
  } = useMapContext();

  const { setMobileView } = useMobileView();
  const [shareOpen, setShareOpen] = useState(false);

  const { dispatch } = useRasterSymbologyContext();

  const isRasterType = !(NON_MAP_DATA_TYPES as readonly string[]).includes(
    dataProduct.data_type
  );
  const isPointCloud = dataProduct.data_type === 'point_cloud';

  // Likes are member-only; non-members (e.g. anonymous /explore) see a
  // read-only count. The like button stops click propagation so liking never
  // activates the card (clicking elsewhere on the card still does). The
  // engagement sits in the card's title row in a fixed spot/size regardless of
  // whether the card is expanded.
  const interactive = Boolean(activeProject?.role);
  const { engagement, toggleLike } = useDataProductLike(
    dataProduct,
    activeProject?.id,
    dataProduct.flight_id
  );

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
      hover={!isPointCloud}
      active={
        activeDataProduct !== null && dataProduct.id === activeDataProduct.id
      }
      data-product-id={dataProduct.id}
    >
      <div className="text-slate-600 text-sm">
        {isPointCloud ? (
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between gap-2">
              <span className="font-bold">
                {getDataProductName(dataProduct.data_type)}
              </span>
              <EngagementInline
                engagement={engagement}
                onToggleLike={toggleLike}
                interactive={interactive}
                size="sm"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <button
                type="button"
                className="w-full rounded border border-slate-300 px-2 py-1.5 text-left hover:bg-slate-100"
                title={`View ${getDataProductTitle(dataProduct.data_type)} in Potree`}
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
                title={`View ${getDataProductTitle(dataProduct.data_type)} on map`}
                onClick={() => handleViewerSelect('map')}
              >
                <div className="text-xs font-semibold">View on map</div>
                <div className="text-xs text-slate-500">
                  Overlay the point cloud on the map alongside other data layers
                </div>
              </button>
            </div>
            {activeProject?.role && (
              <div className="w-36">
                <Button
                  type="button"
                  size="sm"
                  icon="share2"
                  onClick={() => setShareOpen(true)}
                >
                  Share
                </Button>
                <Modal open={shareOpen} setOpen={setShareOpen} overflow="visible">
                  <RasterSymbologyAccessControls
                    dataProduct={dataProduct}
                    project={activeProject}
                  />
                </Modal>
              </div>
            )}
          </div>
        ) : (
          <div
            className="flex flex-col gap-1.5"
            title={`Activate ${getDataProductTitle(dataProduct.data_type)} layer`}
            onClick={() => {
              // Only (re)activate when this isn't already the active product.
              // Clicking an already-active card must not reset its ready state,
              // which would hide the layer without re-activating it.
              if (!activeDataProduct || dataProduct.id !== activeDataProduct.id) {
                dispatch({
                  type: 'SET_READY_STATE',
                  rasterId: dataProduct.id,
                  payload: false,
                });
                activeDataProductDispatch({
                  type: 'set',
                  payload: dataProduct,
                });
              }
            }}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-bold">
                {getDataProductName(dataProduct.data_type)}
              </span>
              <EngagementInline
                engagement={engagement}
                onToggleLike={toggleLike}
                interactive={interactive}
                size="sm"
              />
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
              <button
                type="button"
                onClick={() => setMobileView('map')}
                className="md:hidden mb-2 text-sm font-semibold text-accent2 hover:text-accent2-dark"
              >
                View on map →
              </button>
              <RasterSymbologySettings />
            </div>
          )}
      </div>
    </LayerCard>
  );
}
