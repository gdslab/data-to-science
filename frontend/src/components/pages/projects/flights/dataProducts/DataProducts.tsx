import { Fragment, useEffect, useState } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';
import {
  CheckCircleIcon,
  CogIcon,
  PhotoIcon,
  TrashIcon,
  XCircleIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/react/24/outline';

import { Button } from '../../../../Buttons';
import Table, { TableBody, TableHead } from '../../../../Table';
import UploadModal from '../../../../UploadModal';

import { useInterval } from '../../../../hooks';

import { DataProductStatus } from '../FlightData';
import HintText from '../../../../HintText';

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

export default function DataProducts({
  data,
  role,
}: {
  data: DataProductStatus[];
  role: string;
}) {
  const { flightId, projectId } = useParams();
  const [open, setOpen] = useState(false);
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

  function isGeoTIFF(dataType: string): boolean {
    return dataType === 'ortho' || dataType === 'dsm';
  }

  const dataProductColumns = ['Data Type', 'Preview', 'File', 'Action'];

  return (
    <div>
      <h2>Data Products</h2>
      {data.length > 0 ? (
        <div className="mt-4">
          <div className="grid grid-rows-3 gap-1">
            <HintText>Keywords:</HintText>
            <HintText>COG - Cloud Optimized GeoTIFF</HintText>
            <HintText>COPC - Cloud Optimized Point Cloud</HintText>
            <HintText>EPT - Entwine Point Tile</HintText>
          </div>
          <Table height={96}>
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
                    {isGeoTIFF(dataset.data_type) ? (
                      <Button
                        size="sm"
                        onClick={() => navigator.clipboard.writeText(dataset.url)}
                      >
                        Copy COG URL
                      </Button>
                    ) : (
                      <a
                        href={dataset.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        download
                      >
                        <Button size="sm">Copy COPC URL</Button>
                      </a>
                    )}
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
                  : data.map(({ id }) => [
                      {
                        key: `action-delete-${id}`,
                        icon: <TrashIcon className="h-4 w-4" />,
                        label: 'Delete',
                        url: '#',
                      },
                    ])
              }
            />
          </Table>
        </div>
      ) : null}
      {role !== 'viewer' ? (
        <div className="my-4 flex justify-center">
          <UploadModal
            apiRoute={`/api/v1/projects/${projectId}/flights/${flightId}/data_products`}
            open={open}
            setOpen={setOpen}
            uploadType="dataProduct"
          />
          <Button size="sm" onClick={() => setOpen(true)}>
            Upload Data Product
          </Button>
        </div>
      ) : null}
    </div>
  );
}
