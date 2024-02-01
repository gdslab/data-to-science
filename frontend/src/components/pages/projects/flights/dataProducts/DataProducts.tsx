import { Fragment, useEffect, useState } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';
import {
  CheckCircleIcon,
  CogIcon,
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

export function getDataProductName(dataType: string): string {
  switch (dataType) {
    case 'dsm':
      return 'DSM';
    case 'ortho':
      return 'Orthomosaic';
    case 'point_cloud':
      return 'Point Cloud';
    default:
      return 'Unknown';
  }
}

export function isGeoTIFF(dataType: string): boolean {
  return dataType === 'ortho' || dataType === 'dsm';
}

export default function DataProducts({
  data,
  role,
}: {
  data: DataProductStatus[];
  role: string;
}) {
  const { flightId, projectId } = useParams();
  const [open, setOpen] = useState(false);
  const [tableView, toggleTableView] = useState<'table' | 'carousel'>('carousel');
  const revalidator = useRevalidator();

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
      ? 5000
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
                role === 'viewer'
                  ? dataProductColumns.slice(0, dataProductColumns.length - 1)
                  : dataProductColumns
              }
            />
            <TableBody
              rows={data.map((dataset) => [
                <div className="h-full flex items-center justify-center">
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
                role === 'viewer'
                  ? undefined
                  : data.map((dataProduct) => [
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
      {role !== 'viewer' ? (
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
