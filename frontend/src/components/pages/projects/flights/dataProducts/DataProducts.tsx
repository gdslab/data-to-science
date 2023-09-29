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

  if (data && data.length > 0) {
    const processing = data.filter(({ status }) => status === 'INPROGRESS');
    useInterval(
      () => {
        revalidator.revalidate();
      },
      processing.length > 0 ? 5000 : null
    );
  }

  return (
    <div>
      <h2>Data Products</h2>
      {data.length > 0 ? (
        <div className="mt-4">
          <Table>
            <TableHead
              columns={[
                'Filename',
                'Data Type',
                'Cloud Optimized GeoTIFF',
                'Preview',
                'Status',
              ]}
            />
            <TableBody
              rows={data.map((dataset) => [
                dataset.original_filename,
                dataset.data_type.toUpperCase(),
                <Button
                  size="sm"
                  onClick={() => navigator.clipboard.writeText(dataset.url)}
                >
                  Copy URL
                </Button>,
                <div className="flex items-center justify-center h-32 w-32">
                  {dataset.status === 'SUCCESS' ? (
                    <img
                      className="w-full max-h-28"
                      src={dataset.url.replace('tif', 'webp')}
                    />
                  ) : (
                    <Fragment>
                      <span className="sr-only">Preview photo not ready</span>
                      <PhotoIcon className="h-24 w-24" />
                    </Fragment>
                  )}
                </div>,
                <div className="flex items-center justify-center">
                  {dataset.status === 'INPROGRESS' ? (
                    <Fragment>
                      <CogIcon
                        className="h-8 w-8 mr-4 animate-spin"
                        aria-hidden="true"
                      />
                      Processing...
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
                </div>,
              ])}
            />
          </Table>
        </div>
      ) : null}
      <div className="my-4">
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
