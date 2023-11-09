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

export default function DataProducts({ data }: { data: DataProductStatus[] }) {
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

  function getDataProductName(dataType: string): string {
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

  return (
    <div>
      <h2>Data Products</h2>
      {data.length > 0 ? (
        <div className="mt-4">
          <div className="grid grid-rows-3 gap-1.5">
            <HintText>Keywords:</HintText>
            <HintText>COG - Cloud Optimized GeoTIFF</HintText>
            <HintText>EPT - Entwine Point Tile</HintText>
          </div>
          <Table>
            <TableHead columns={['Data Type', 'Preview', 'File', 'Action']} />
            <TableBody
              rows={data.map((dataset) => [
                getDataProductName(dataset.data_type),
                <div className="flex items-center justify-center h-32 w-32">
                  {dataset.status === 'SUCCESS' && isGeoTIFF(dataset.data_type) ? (
                    <img
                      className="w-full max-h-28"
                      src={dataset.url.replace('tif', 'webp')}
                    />
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
                  <div className="flex justify-center">
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
                        <Button size="sm">Download</Button>
                      </a>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    {dataset.status === 'INPROGRESS' ? (
                      <Fragment>
                        <CogIcon
                          className="h-8 w-8 mr-4 animate-spin"
                          aria-hidden="true"
                        />
                        {isGeoTIFF(dataset.data_type)
                          ? 'Generating COG...'
                          : 'Generating EPT...'}
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
              actions={data.map(({ id }) => [
                {
                  key: `action-delete-${id}`,
                  icon: <TrashIcon className="h-4 w-4" />,
                  label: 'Delete',
                  url: '#',
                },
              ])}
            />
          </Table>
        </div>
      ) : (
        <Fragment></Fragment>
      )}
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
    </div>
  );
}
