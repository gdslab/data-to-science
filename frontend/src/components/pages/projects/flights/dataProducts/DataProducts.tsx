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

  return (
    <div>
      <h2>Data Products</h2>
      {data.length > 0 ? (
        <div className="mt-4">
          <Table>
            <TableHead
              columns={['Data Type', 'Preview', 'Cloud Optimized GeoTIFF', 'Action']}
            />
            <TableBody
              rows={data.map((dataset) => [
                dataset.data_type.toUpperCase(),
                <div className="flex items-center justify-center h-32 w-32">
                  {dataset.status === 'SUCCESS' ? (
                    <img
                      className="w-full max-h-28"
                      src={dataset.url.replace('tif', 'webp')}
                    />
                  ) : (
                    <div>
                      <span className="sr-only">Preview photo not ready</span>
                      <PhotoIcon className="h-24 w-24" />
                    </div>
                  )}
                </div>,
                dataset.status === 'SUCCESS' ? (
                  <div className="flex justify-center">
                    <Button
                      size="sm"
                      onClick={() => navigator.clipboard.writeText(dataset.url)}
                    >
                      Copy URL
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    {dataset.status === 'INPROGRESS' ? (
                      <Fragment>
                        <CogIcon
                          className="h-8 w-8 mr-4 animate-spin"
                          aria-hidden="true"
                        />
                        Generating COG...
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
          uploadType="tif"
        />
        <Button size="sm" onClick={() => setOpen(true)}>
          Upload Data Product (.tif)
        </Button>
      </div>
    </div>
  );
}
