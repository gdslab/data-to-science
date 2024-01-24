import { useState } from 'react';
import { EyeIcon, CogIcon, PhotoIcon, TrashIcon } from '@heroicons/react/24/outline';

import Card from '../../../../Card';
import { DataProductStatus } from '../FlightData';
import { isGeoTIFF } from './DataProducts';

function ProgressBar() {
  return (
    <div className="w-full">
      <div className="h-1.5 w-full bg-green-100 rounded-b-lg overflow-hidden">
        <div className="animate-progress w-full h-full bg-green-500 origin-left-right"></div>
      </div>
    </div>
  );
}

export default function DataProductCard({
  dataProduct,
  userRole,
}: {
  dataProduct: DataProductStatus;
  userRole: string;
}) {
  const [isCopied, setIsCopied] = useState(false);

  return (
    <div className="flex items-center justify-center">
      <div className="relative w-80 p-1.5">
        <Card rounded={true}>
          <div className="grid grid-flow-row auto-rows-max gap-2">
            {/* preview image */}
            <div className="relative flex items-center justify-center bg-accent3/20">
              {dataProduct.status === 'SUCCESS' && isGeoTIFF(dataProduct.data_type) ? (
                <div className="flex items-center justify-center w-full h-40">
                  <img
                    className="object-scale-down h-full"
                    src={dataProduct.url.replace('tif', 'jpg')}
                    alt="Preview of data product"
                  />
                  <div
                    className="absolute bottom-0 w-full text-center text-white p-1 bg-accent3/80 cursor-pointer"
                    onClick={() => {
                      navigator.clipboard.writeText(dataProduct.url);
                      setIsCopied(true);
                      setTimeout(() => {
                        setIsCopied(false);
                      }, 3000);
                    }}
                  >
                    {isCopied ? 'Copied to clipboard' : 'Click to Copy URL'}
                  </div>
                </div>
              ) : dataProduct.status === 'SUCCESS' &&
                dataProduct.data_type === 'point_cloud' ? (
                <div className="flex w-full h-40">
                  <div className="m-4 w-full h-full bg-white flex flex-wrap items-center justify-center">
                    add stock point cloud img
                  </div>
                  <div
                    className="absolute bottom-0 w-full text-center text-white p-1 bg-accent3/80 cursor-pointer"
                    onClick={() => {
                      navigator.clipboard.writeText(dataProduct.url);
                      setIsCopied(true);
                      setTimeout(() => {
                        setIsCopied(false);
                      }, 3000);
                    }}
                  >
                    {isCopied ? 'Copied to clipboard' : 'Click to Copy URL'}
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center w-full h-48 bg-white">
                  <span className="sr-only">Preview not available</span>
                  <PhotoIcon className="w-full" />
                </div>
              )}
            </div>
            {/* data product details */}
            <div className="flex items-center justify-between text-lg">
              <span>{dataProduct.data_type.split('_').join(' ').toUpperCase()}</span>
              {userRole !== 'viewer' ? (
                <div onClick={() => alert('not implemented')}>
                  <span className="sr-only">Delete</span>
                  <TrashIcon className="w-4 h-4 text-red-600 cursor-pointer" />
                </div>
              ) : null}
            </div>
            {/* action buttons */}
            <div className="flex items-center justify-around gap-4">
              <div
                className="flex items-center gap-2 text-sky-600 cursor-pointer"
                onClick={() => {
                  alert('not implemented yet');
                }}
              >
                <EyeIcon className="h-6 w-6" />
                <span>View</span>
              </div>
              <span className="text-slate-300">|</span>
              <div
                className="flex items-center gap-2 text-sky-600 cursor-pointer"
                onClick={() => {
                  alert('not implemented yet');
                }}
              >
                <CogIcon className="h-6 w-6" />
                <span>Processing</span>
              </div>
            </div>
          </div>
        </Card>
        {dataProduct.status === 'INPROGRESS' ? (
          <div className="w-full absolute bottom-0">
            <ProgressBar />
          </div>
        ) : null}
      </div>
    </div>
  );
}
