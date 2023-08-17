import axios from 'axios';
import { Params, useLoaderData } from 'react-router-dom';

import { Flight } from '../ProjectDetail/ProjectDetail';
import { Table, TableBody, TableHead } from '../ProjectDetail/ProjectDetail';

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

interface Data {}

interface FlightData {
  flight: Flight;
  data: Data;
}

export default function FlightData() {
  const { flight, data } = useLoaderData();

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
            <TableHead
              columns={['Platform', 'Sensor', 'Acquisition Date', 'Actions']}
            />
            <TableBody
              rows={[
                flight.platform,
                flight.sensor,
                flight.acquisition_date.toString(),
              ]}
            />
          </Table>
        </div>
      </div>
    );
  } else {
    return null;
  }
}
