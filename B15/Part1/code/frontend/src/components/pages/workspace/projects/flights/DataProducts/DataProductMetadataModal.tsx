import { useState } from 'react';
import { InformationCircleIcon } from '@heroicons/react/24/outline';

import Modal from '../../../../../Modal';
import { DataProduct } from '../../Project';

export default function DataProductMetadataModal({
  dataProduct,
  iconOnly = true,
}: {
  dataProduct: DataProduct;
  iconOnly?: boolean;
}) {
  const [openMetadataModal, setOpenMetadataModal] = useState(false);

  const isRasterType = !['point_cloud', 'panoramic', '3dgs'].includes(
    dataProduct.data_type
  );

  // Don't render if not a raster type or missing metadata
  if (
    !isRasterType ||
    (!dataProduct.resolution && !dataProduct.crs && !dataProduct.bbox)
  ) {
    return null;
  }

  const displayUnit =
    dataProduct.resolution?.unit === 'unknown'
      ? 'unknown or degrees'
      : dataProduct.resolution?.unit;

  return (
    <div>
      <div>
        {iconOnly ? (
          <div
            className="cursor-pointer"
            onClick={() => setOpenMetadataModal(true)}
          >
            <span className="sr-only">View metadata</span>
            <InformationCircleIcon className="w-5 h-5 cursor-pointer hover:scale-110" />
          </div>
        ) : null}
      </div>
      <Modal open={openMetadataModal} setOpen={setOpenMetadataModal}>
        <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
          <div className="sm:flex sm:items-start">
            <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
              <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
                Raster Metadata
              </h3>
              <div className="mt-2 space-y-3 text-sm text-gray-600">
                {dataProduct.resolution && dataProduct.crs && (
                  <div>
                    <span className="font-semibold">Resolution:</span>{' '}
                    {parseFloat(dataProduct.resolution.x.toFixed(6))} x{' '}
                    {parseFloat(dataProduct.resolution.y.toFixed(6))}{' '}
                    {displayUnit}
                  </div>
                )}

                {dataProduct.crs && (
                  <div>
                    <span className="font-semibold">EPSG:</span>{' '}
                    {dataProduct.crs.epsg}
                  </div>
                )}

                {dataProduct.bbox && (
                  <div>
                    <span className="font-semibold">Bounding Box:</span>
                    <div className="mt-1 pl-4 font-mono text-xs">
                      <div>Min X: {dataProduct.bbox[0].toFixed(8)}</div>
                      <div>Min Y: {dataProduct.bbox[1].toFixed(8)}</div>
                      <div>Max X: {dataProduct.bbox[2].toFixed(8)}</div>
                      <div>Max Y: {dataProduct.bbox[3].toFixed(8)}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
          <button
            type="button"
            className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-xs ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
            onClick={() => setOpenMetadataModal(false)}
          >
            Close
          </button>
        </div>
      </Modal>
    </div>
  );
}
