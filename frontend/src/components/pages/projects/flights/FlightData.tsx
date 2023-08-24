import axios from 'axios';
import { Fragment, useState } from 'react';
import { Params, useLoaderData, useParams, useRevalidator } from 'react-router-dom';
import {
  CheckCircleIcon,
  CogIcon,
  XCircleIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/react/24/outline';

import { Button } from '../../../Buttons';
import { useInterval } from '../../../hooks';
import UploadModal from '../../../UploadModal';
import { Flight } from '../ProjectDetail';
import Table, { TableBody, TableHead } from '../../../Table';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const flight = await axios.get(
      `/api/v1/projects/${params.projectId}/flights/${params.flightId}`
    );
    const flightData = await axios.get(
      `/api/v1/projects/${params.projectId}/flights/${params.flightId}/raw_data`
    );
    if (flight && flightData) {
      return { flight: flight.data, data: flightData.data };
    } else {
      return { flight: null, data: [] };
    }
  } catch (err) {
    console.error('Unable to retrieve flight data');
    return { flight: null, data: [] };
  }
}

interface Data {
  original_filename: string;
  url: string;
  status: string;
}

interface FlightData {
  flight: Flight;
  data: Data[];
}

export default function FlightData() {
  const { flight, data } = useLoaderData() as FlightData;
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

  if (flight) {
    return (
      <div className="mx-4">
        <div className="mt-4">
          <div>
            <h1>Flight</h1>
          </div>
        </div>
        <div className="mt-4">
          <Table>
            <TableHead columns={['Platform', 'Sensor', 'Acquisition Date']} />
            <TableBody
              rows={[
                [flight.platform, flight.sensor, flight.acquisition_date.toString()],
              ]}
            />
          </Table>
        </div>
        <div className="mt-4">
          <h2>Raw Data</h2>
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
          <div className="my-4">
            <UploadModal
              open={open}
              setOpen={setOpen}
              apiRoute={`/api/v1/projects/${projectId}/flights/${flightId}/raw_data`}
            />
            <Button size="sm" onClick={() => setOpen(true)}>
              Upload raw data (.tif)
            </Button>
          </div>
        </div>
      </div>
    );
  } else {
    return null;
  }
}
