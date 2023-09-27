import axios from 'axios';
import { Link, Params, useLoaderData, useParams } from 'react-router-dom';

import { Button } from '../../Buttons';
import Table, { TableBody, TableHead } from '../../Table';

import { DefaultSymbologySettings } from '../../maps/MapContext';

interface Project {
  id: string;
  title: string;
  description: string;
  planting_date: string;
  harvest_date: string;
  location_id: string;
  team_id: string;
}

export interface Band {
  data_type: string;
  nodata: string | null;
  stats: {
    mean: number;
    stddev: number;
    maximum: number;
    minimum: number;
  };
  unit: string;
}

export interface DataProduct {
  id: string;
  band_info: {
    bands: Band[];
  };
  data_type: string;
  original_filename: string;
  filepath: string;
  url: string;
  flight_id: string;
  user_style: null | DefaultSymbologySettings;
}

export interface Flight {
  id: string;
  acquisition_date: Date;
  altitude: number;
  side_overlap: number;
  forward_overlap: number;
  sensor: string;
  platform: string;
  project_id: string;
  pilot_id: string;
  data_products: DataProduct[];
}

interface ProjectData {
  project: Project;
  flights: Flight[];
}

export async function loader({ params }: { params: Params<string> }) {
  const project = await axios.get(`/api/v1/projects/${params.projectId}`);
  const flights = await axios.get(`/api/v1/projects/${params.projectId}/flights`);
  if (project && flights) {
    return { project: project.data, flights: flights.data };
  } else {
    return null;
  }
}

export default function ProjectDetail() {
  const { projectId } = useParams();
  const { project, flights } = useLoaderData() as ProjectData;

  return (
    <div className="mx-4">
      <div className="mt-4">
        <div>
          <h1>{project.title}</h1>
          <span className="text-gray-600">{project.description}</span>
        </div>
      </div>
      <div className="mt-4">
        <h2>Datasets</h2>
        {flights ? (
          <div>
            <h3>Flights</h3>
            <Table>
              <TableHead
                columns={['Platform', 'Sensor', 'Acquisition Date', 'Actions']}
              />
              <TableBody
                rows={flights.map((flight) => [
                  flight.platform,
                  flight.sensor,
                  flight.acquisition_date.toString(),
                ])}
                actions={flights.map((flight, i) => [
                  {
                    key: `action-edit-${i}`,
                    label: 'Edit',
                    url: `/projects/${projectId}/flights/${flight.id}/edit`,
                  },
                  {
                    key: `action-data-${i}`,
                    label: 'Raw Data',
                    url: `/projects/${projectId}/flights/${flight.id}/raw`,
                  },
                  {
                    key: `action-products-${i}`,
                    label: 'Data Product',
                    url: `/projects/${projectId}/flights/${flight.id}/products`,
                  },
                ])}
              />
            </Table>
          </div>
        ) : (
          <em>No datasets associated with project</em>
        )}
      </div>
      <div className="mt-4">
        <Link to={`/projects/${projectId}/flights/create`}>
          <Button>Add New Flight</Button>
        </Link>
      </div>
    </div>
  );
}
