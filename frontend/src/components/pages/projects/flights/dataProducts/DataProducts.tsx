import axios from 'axios';
import { Fragment, useState } from 'react';
import { Params, useLoaderData, useParams, useRevalidator } from 'react-router-dom';
import {
  CheckCircleIcon,
  CogIcon,
  XCircleIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/react/24/outline';

import { Button } from '../../../../Buttons';
import Table, { TableBody, TableHead } from '../../../../Table';
import UploadModal from '../../../../UploadModal';

import { useInterval } from '../../../../hooks';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const flightData = await axios.get(
      `/api/v1/projects/${params.projectId}/flights/${params.flightId}/data_products`
    );
    if (flightData) {
      return flightData.data;
    } else {
      return [];
    }
  } catch (err) {
    console.error('Unable to retrieve flight data');
    return [];
  }
}

interface Data {
  original_filename: string;
  url: string;
  status: string;
}

export default function DataProducts() {
  const data = useLoaderData() as Data[];
  const { flightId, projectId } = useParams();
  const [open, setOpen] = useState(false);
  const revalidator = useRevalidator();

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
    <div className="mt-4">
      <h2>Data Products</h2>
      <div className="mt-4">
        <Table>
          <TableHead
            columns={['Filename', 'Cloud Optimized GeoTIFF', 'Preview', 'Status']}
          />
          <TableBody
            rows={data.map((dataset) => [
              dataset.original_filename,
              <Button
                size="sm"
                onClick={() => navigator.clipboard.writeText(dataset.url)}
              >
                Copy URL
              </Button>,
              <div className="flex items-center justify-center h-32 w-32">
                <img
                  className="w-full max-h-28"
                  src={dataset.url.replace('tif', 'webp')}
                />
              </div>,
              <div className="flex items-center justify-center">
                {dataset.status === 'INPROGRESS' ? (
                  <Fragment>
                    <CogIcon className="h-8 w-8 mr-4 animate-spin" aria-hidden="true" />
                    Processing...
                  </Fragment>
                ) : dataset.status === 'FAILED' ? (
                  <Fragment>
                    <XCircleIcon className="h-8 h-8 mr-4 text-red-500" />
                    Failed
                  </Fragment>
                ) : dataset.status === 'SUCCESS' ? (
                  <Fragment>
                    <CheckCircleIcon className="h-8 w-8 mr-4 text-green-500" /> Success
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
