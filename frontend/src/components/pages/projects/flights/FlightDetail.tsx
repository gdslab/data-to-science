import axios from 'axios';
import { Outlet, Params, useLoaderData } from 'react-router-dom';

import { Flight } from '../ProjectDetail';
import Table, { TableBody, TableHead } from '../../../Table';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const flight = await axios.get(
      `/api/v1/projects/${params.projectId}/flights/${params.flightId}`
    );
    if (flight) {
      return flight.data;
    } else {
      return null;
    }
  } catch (err) {
    console.error('Unable to retrieve flight data');
    return null;
  }
}

export default function FlightDetail() {
  const flight = useLoaderData() as Flight;

  if (flight) {
    return (
      <div className="mx-4">
        <div className="mt-4">
          <div>
            <h1>Flight</h1>
          </div>
        </div>
        <div className="my-4">
          <Table>
            <TableHead columns={['Platform', 'Sensor', 'Acquisition Date']} />
            <TableBody
              rows={[
                [
                  flight.platform.replace(/_/g, ' '),
                  flight.sensor,
                  new Date(flight.acquisition_date).toLocaleDateString('en-US'),
                ],
              ]}
            />
          </Table>
        </div>
        <Outlet />
      </div>
    );
  } else {
    return null;
  }
}
