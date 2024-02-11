import { Fragment, useEffect, useState } from 'react';
import { useNavigate, useParams, useRevalidator } from 'react-router-dom';
import {
  CheckCircleIcon,
  CogIcon,
  EyeIcon,
  PhotoIcon,
  XCircleIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/react/24/outline';

import { Button } from '../../../../Buttons';
import Table, { TableBody, TableHead } from '../../../../Table';
import TableCardRadioInput from '../../../../TableCardRadioInput';
import UploadModal from '../../../../UploadModal';

import { useInterval } from '../../../../hooks';

import { DataProductStatus } from '../FlightData';
import DataProductCard from './DataProductCard';
import DataProductDeleteModal from './DataProductDeleteModal';
import { useProjectContext } from '../../ProjectContext';

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

export function isGeoTIFF(dataType: string): boolean {
  return dataType !== 'point_cloud';
}

export default function DataProducts({ data }: { data: DataProductStatus[] }) {
  const { flightId, projectId } = useParams();
  const [open, setOpen] = useState(false);
  const [tableView, toggleTableView] = useState<'table' | 'carousel'>('carousel');
  const revalidator = useRevalidator();
  const { project, projectRole } = useProjectContext();
  const navigate = useNavigate();

  useEffect(() => {
    if (!open) revalidator.revalidate();
  }, [open]);

  useInterval(
    () => {
      revalidator.revalidate();
    },
    data &&
      data.length > 0 &&
      data.filter(({ status }) => status === 'INPROGRESS').length > 0
      ? 30000 // 30 seconds
      : null
  );

  const dataProductColumns = ['Data Type', 'Preview', 'File', 'Action'];

  return (
    <div className="h-full flex flex-col">
      <div className="h-24">
        <h2>Data Products</h2>
        <TableCardRadioInput tableView={tableView} toggleTableView={toggleTableView} />
      </div>
      {data.length > 0 ? (
        tableView === 'table' ? (
          <Table>
            <TableHead
              columns={
                projectRole === 'viewer'
                  ? dataProductColumns.slice(0, dataProductColumns.length - 1)
                  : dataProductColumns
              }
            />
            <TableBody
              rows={data.map((dataset) => [
                <div
                  key={`row-${dataset.id}`}
                  className="h-full flex items-center justify-center"
                >
                  {getDataProductName(dataset.data_type)}
                </div>,
                <div className="h-full flex items-center justify-center">
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
                  <div className="h-full flex items-center justify-center">
                    <Button
                      size="sm"
                      onClick={() => navigator.clipboard.writeText(dataset.url)}
                    >
                      {isGeoTIFF(dataset.data_type) ? 'Copy COG URL' : 'Copy COPC URL'}
                    </Button>
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center">
                    {dataset.status === 'INPROGRESS' ? (
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
              ])}
              actions={
                projectRole !== 'owner'
                  ? data.map((dataProduct) => [
                      {
                        key: `action-view-${dataProduct.id}`,
                        type: 'component',
                        component: (
                          <div
                            className="flex items-center gap-2 text-sky-600 cursor-pointer"
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
                      },
                    ])
                  : data.map((dataProduct) => [
                      {
                        key: `action-view-${dataProduct.id}`,
                        type: 'component',
                        component: (
                          <div
                            className="flex items-center gap-2 text-sky-600 cursor-pointer"
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
                      },
                      {
                        key: `action-delete-${dataProduct.id}`,
                        type: 'component',
                        component: (
                          <DataProductDeleteModal
                            dataProduct={dataProduct}
                            tableView={true}
                          />
                        ),
                        label: 'Delete',
                      },
                    ])
              }
            />
          </Table>
        ) : (
          <div className="grow flex flex-cols flex-wrap justify-start gap-4 min-h-96 overflow-auto">
            {data.map((dataProduct) => (
              <DataProductCard key={dataProduct.id} dataProduct={dataProduct} />
            ))}
          </div>
        )
      ) : null}
      {projectRole !== 'viewer' ? (
        <div className="my-4 flex justify-center">
          <UploadModal
            apiRoute={`/api/v1/projects/${projectId}/flights/${flightId}`}
            open={open}
            setOpen={setOpen}
          />
          <Button size="sm" onClick={() => setOpen(true)}>
            Upload Data
          </Button>
        </div>
      ) : null}
    </div>
  );
}
