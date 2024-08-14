import { Fragment, useState } from 'react';
import { NavigateFunction, useNavigate } from 'react-router-dom';
import {
  ArrowDownTrayIcon,
  CheckCircleIcon,
  CogIcon,
  EyeIcon,
  PhotoIcon,
  XCircleIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/react/24/outline';

import { Status } from '../../../../Alert';
import { CopyURLButton } from '../../../../Buttons';
import DataProductDeleteModal from './DataProductDeleteModal';
import { useProjectContext } from '../../ProjectContext';
import { Project } from '../../ProjectList';
import Table, { TableBody, TableHead } from '../../../../Table';
import ToolboxModal from './ToolboxModal';
import DataProductShareModal from './DataProductShareModal';

import { DataProduct } from '../../Project';
import EditableDataType from './EditableDataType';

export function isGeoTIFF(dataType: string): boolean {
  return dataType !== 'point_cloud';
}

export function getDataProductName(dataType: string): string {
  switch (dataType) {
    case 'dsm':
      return 'DSM';
    case 'ortho':
      return 'Orthomosaic';
    case 'point_cloud':
      return 'Point Cloud';
    default:
      return dataType;
  }
}

function getDataProductActions(
  role: string | undefined,
  data: DataProduct[],
  navigate: NavigateFunction,
  project: Project | null
) {
  const getDeleteAction = (dataProduct: DataProduct) => ({
    key: `action-delete-${dataProduct.id}`,
    type: 'component',
    component: <DataProductDeleteModal dataProduct={dataProduct} tableView={true} />,
    label: 'Delete',
  });

  const getToolboxAction = (dataProduct: DataProduct) => ({
    key: `action-toolbox-${dataProduct.id}`,
    type: 'component',
    component: <ToolboxModal dataProduct={dataProduct} tableView={true} />,
    label: 'Toolbox',
  });

  const getDownloadAction = (dataProduct: DataProduct) => ({
    key: `action-download-${dataProduct.id}`,
    type: 'component',
    component: (
      <a
        className="flex items-center gap-1 text-sky-600"
        href={dataProduct.url}
        target="_blank"
        download
      >
        <ArrowDownTrayIcon className="w-4 h-4" title="Download data product" />
        <span className="text-sm">Download</span>
      </a>
    ),
    label: 'Download',
  });

  const getShareAction = (dataProduct: DataProduct) => ({
    key: `action-share-${dataProduct.id}`,
    type: 'component',
    component: <DataProductShareModal dataProduct={dataProduct} tableView={true} />,
    label: 'Share',
  });

  const getViewAction = (dataProduct: DataProduct) => ({
    key: `action-view-${dataProduct.id}`,
    type: 'component',
    component: (
      <div
        className="flex items-center gap-1 text-sky-600 cursor-pointer"
        onClick={() => {
          navigate('/home', {
            state: { project: project, dataProduct: dataProduct },
          });
        }}
      >
        <EyeIcon className="h-4 w-4" />
        <span className="text-sm">View</span>
      </div>
    ),
    label: 'View',
  });

  if (role === 'owner') {
    return data.map((dataProduct) => [
      getViewAction(dataProduct),
      getToolboxAction(dataProduct),
      getDownloadAction(dataProduct),
      getShareAction(dataProduct),
      getDeleteAction(dataProduct),
    ]);
  } else if (role === 'manager') {
    return data.map((dataProduct) => [
      getViewAction(dataProduct),
      getDownloadAction(dataProduct),
      getToolboxAction(dataProduct),
    ]);
  } else {
    return data.map((dataProduct) => [getViewAction(dataProduct)]);
  }
}

function DataTypeSelect({
  dataProduct,
  isLastRow,
  setStatus,
}: {
  dataProduct: DataProduct;
  isLastRow: boolean;
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
}) {
  const [isEditing, setIsEditing] = useState(false);

  return (
    <EditableDataType
      dataProduct={dataProduct}
      isEditing={isEditing}
      menuPlacement={isLastRow ? 'top' : 'bottom'}
      setIsEditing={setIsEditing}
      setStatus={setStatus}
    />
  );
}

export default function DataProductsTable({
  data,
  setStatus,
}: {
  data: DataProduct[];
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
}) {
  const navigate = useNavigate();
  const { project, projectRole } = useProjectContext();

  const dataProductColumns = ['Data Type', 'Preview', 'File', 'Action'];

  if (data.length > 0) {
    return (
      <div className="overflow-x-auto">
        <div className="min-w-[1000px]">
          <Table>
            <TableHead
              columns={
                projectRole === 'viewer'
                  ? dataProductColumns.slice(0, dataProductColumns.length - 1)
                  : dataProductColumns
              }
            />
            <div className="overflow-y-auto min-h-96 max-h-96 xl:max-h-[420px] 2xl:max-h-[512px]">
              <TableBody
                rows={data.map((dataset, index) => ({
                  key: dataset.id,
                  values: [
                    <div
                      key={`row-${dataset.id}-datatype`}
                      className="h-full w-full flex items-center justify-center"
                    >
                      <DataTypeSelect
                        dataProduct={dataset}
                        isLastRow={index === data.length - 1}
                        setStatus={setStatus}
                      />
                    </div>,
                    <div
                      key={`row-${dataset.id}-preview`}
                      className="h-full flex items-center justify-center"
                    >
                      {dataset.status === 'SUCCESS' && isGeoTIFF(dataset.data_type) ? (
                        <div className="h-full">
                          <img
                            className="w-full max-h-28"
                            src={dataset.url.replace('tif', 'jpg')}
                            alt="Preview of data product"
                          />
                        </div>
                      ) : isGeoTIFF(dataset.data_type) ? (
                        <div>
                          <span className="sr-only">Preview photo not ready</span>
                          <PhotoIcon className="h-24 w-24" />
                        </div>
                      ) : (
                        <div>No preview</div>
                      )}
                    </div>,
                    dataset.status === 'SUCCESS' ? (
                      <div
                        key={`row-${dataset.id}-file`}
                        className="h-full flex items-center justify-center"
                      >
                        <CopyURLButton
                          copyText="Copy File URL"
                          copiedText="Copied"
                          url={dataset.url}
                        />
                      </div>
                    ) : (
                      <div
                        key={`row-${dataset.id}-file`}
                        className="h-full flex items-center justify-center"
                      >
                        {dataset.status === 'INPROGRESS' ||
                        dataset.status === 'WAITING' ? (
                          <Fragment>
                            <CogIcon
                              className="h-8 w-8 mr-4 animate-spin"
                              aria-hidden="true"
                            />
                            {isGeoTIFF(dataset.data_type)
                              ? 'Generating COG'
                              : 'Generating EPT & COPC'}
                          </Fragment>
                        ) : dataset.status === 'FAILED' ? (
                          <Fragment>
                            <XCircleIcon className="h-8 h-8 mr-4 text-red-500" />
                            Failed
                          </Fragment>
                        ) : dataset.status === 'SUCCESS' ? (
                          <Fragment>
                            <CheckCircleIcon className="h-8 w-8 mr-4 text-green-500" />{' '}
                            Success
                          </Fragment>
                        ) : (
                          <Fragment>
                            <QuestionMarkCircleIcon className="h-8 w-8 mr-4" />
                            Unknown
                          </Fragment>
                        )}
                      </div>
                    ),
                  ],
                }))}
                actions={getDataProductActions(projectRole, data, navigate, project)}
              />
            </div>
          </Table>
        </div>
      </div>
    );
  } else {
    return null;
  }
}
