import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowDownTrayIcon,
  ExclamationCircleIcon,
  EyeIcon,
  PhotoIcon,
} from '@heroicons/react/24/outline';

import { Status } from '../../../../Alert';
import Card from '../../../../Card';
import { isGeoTIFF } from './DataProductsTable';
import DataProductDeleteModal from './DataProductDeleteModal';
import EditableDataType from './EditableDataType';
import ToolboxModal from './ToolboxModal';
import { useProjectContext } from '../../ProjectContext';
import DataProductShareModal from './DataProductShareModal';

import { DataProduct } from '../../Project';

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
  otherDataProducts,
  setStatus,
}: {
  dataProduct: DataProduct;
  otherDataProducts: DataProduct[];
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
}) {
  const [invalidPreviews, setInvalidPreviews] = useState<string[]>([]);
  const [isCopied, setIsCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const { project, projectRole } = useProjectContext();
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-center min-h-80">
      <div className="relative w-80 overflow-hidden">
        <Card rounded={true}>
          <div className="grid grid-flow-row auto-rows-max gap-2 relative">
            {/* preview image */}
            <div className="relative flex items-center justify-center bg-accent3/20">
              {dataProduct.status === 'SUCCESS' &&
              isGeoTIFF(dataProduct.data_type) ? (
                <div className="flex items-center justify-center w-full h-48">
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
                <div className="flex items-center justify-center w-full h-48">
                  {invalidPreviews.indexOf(dataProduct.id) < 0 ? (
                    <img
                      className="object-scale-down h-full"
                      src={dataProduct.url.replace('copc.laz', 'png')}
                      alt="Preview of data product"
                      onError={() => {
                        setInvalidPreviews([
                          ...invalidPreviews,
                          dataProduct.id,
                        ]);
                      }}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <span>Generating preview...</span>
                      <PhotoIcon className="h-1/2" />
                    </div>
                  )}
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
              ) : dataProduct.status === 'FAILED' ? (
                <div className="flex items-center justify-center w-full h-48">
                  <span className="sr-only">Process failed</span>
                  <ExclamationCircleIcon className="h-full text-accent2" />
                  <span>
                    An error occurred while processing the uploaded data product
                  </span>
                </div>
              ) : (
                <div className="flex items-center justify-center w-full h-48 bg-white">
                  <span className="sr-only">Preview not available</span>
                  <PhotoIcon className="h-full" />
                </div>
              )}
            </div>
            {/* data product details */}
            <div className="h-10 flex items-center justify-between text-lg">
              <EditableDataType
                dataProduct={dataProduct}
                isEditing={isEditing}
                menuPlacement="top"
                setIsEditing={setIsEditing}
                setStatus={setStatus}
              />
              {!isEditing && (
                <div className="flex flex-row gap-4">
                  <a href={dataProduct.url} target="_blank" download>
                    <ArrowDownTrayIcon
                      className="w-5 h-5"
                      title="Download data product"
                    />
                  </a>
                  {projectRole === 'owner' && (
                    <>
                      <DataProductShareModal dataProduct={dataProduct} />
                      <DataProductDeleteModal dataProduct={dataProduct} />
                    </>
                  )}
                </div>
              )}
            </div>
            {/* action buttons */}
            <div className="flex items-center justify-around gap-4 relative">
              <div
                className="flex items-center gap-2 text-sky-600 cursor-pointer"
                onClick={() => {
                  navigate('/home', {
                    state: {
                      project: project,
                      dataProduct: dataProduct,
                      navContext: 'dataProductCard',
                    },
                  });
                }}
              >
                <EyeIcon className="h-6 w-6" />
                <span>View</span>
              </div>
              {(projectRole === 'manager' || projectRole === 'owner') && (
                <>
                  <span className="text-slate-300">|</span>
                  <ToolboxModal
                    dataProduct={dataProduct}
                    otherDataProducts={otherDataProducts}
                  />
                </>
              )}
            </div>
          </div>
        </Card>
        {dataProduct.status === 'INPROGRESS' ||
        dataProduct.status === 'WAITING' ? (
          <div className="w-full absolute bottom-0 left-0">
            <ProgressBar />
          </div>
        ) : null}
      </div>
    </div>
  );
}
