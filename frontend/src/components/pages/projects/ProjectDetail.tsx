import axios from 'axios';
import { useState } from 'react';
import { Link, Params, useLoaderData, useParams } from 'react-router-dom';
import { TrashIcon, PencilIcon } from '@heroicons/react/24/outline';

import { Button } from '../../Buttons';
import FlightForm from './flights/FlightForm';
import Modal from '../../Modal';
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

export interface EO {
  name: string;
  description: string;
}

export interface DataProduct {
  id: string;
  data_type: string;
  original_filename: string;
  filepath: string;
  url: string;
  flight_id: string;
  stac_properties: {
    raster: Band[];
    eo: EO[];
  };
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

export interface Pilot {
  label: string;
  value: string;
}

interface ProjectData {
  pilots: Pilot[];
  project: Project;
  flights: Flight[];
}

export async function loader({ params }: { params: Params<string> }) {
  const pilots = await axios.get(`/api/v1/projects/${params.projectId}/members`);
  const project = await axios.get(`/api/v1/projects/${params.projectId}`);
  const flights = await axios.get(`/api/v1/projects/${params.projectId}/flights`);
  if (pilots && project && flights) {
    return { pilots: pilots.data, project: project.data, flights: flights.data };
  } else {
    return null;
  }
}

export default function ProjectDetail() {
  const [open, setOpen] = useState(false);
  const { projectId } = useParams();
  const { pilots, project, flights } = useLoaderData() as ProjectData;

  return (
    <div className="mx-4">
      <div className="mt-4">
        <div>
          <h1>{project.title}</h1>
          <span className="text-gray-600">{project.description}</span>
        </div>
      </div>
      <div className="mt-4">
        <h2>Flights</h2>
        {flights.length > 0 ? (
          <Table>
            <TableHead
              columns={['Platform', 'Sensor', 'Acquisition Date', 'Data', 'Actions']}
            />
            <TableBody
              rows={flights.map((flight) => [
                flight.platform.replace(/_/g, ' '),
                flight.sensor,
                new Date(flight.acquisition_date).toLocaleDateString('en-US'),
                <Link
                  className="text-sky-600"
                  to={`/projects/${projectId}/flights/${flight.id}/data`}
                >
                  View Data
                </Link>,
              ])}
              actions={flights.map((flight, i) => [
                {
                  key: `action-edit-${i}`,
                  icon: <PencilIcon className="h-4 w-4" />,
                  label: 'Edit',
                  url: `/projects/${projectId}/flights/${flight.id}/edit`,
                },
                {
                  key: `action-delete-${i}`,
                  icon: <TrashIcon className="h-4 w-4" />,
                  label: 'Delete',
                  url: '#',
                },
              ])}
            />
          </Table>
        ) : null}
      </div>
      {projectId ? (
        <div className="mt-4 flex justify-center">
          <Button onClick={() => setOpen(true)}>Add New Flight</Button>
          <Modal open={open} setOpen={setOpen}>
            <FlightForm projectId={projectId} setOpen={setOpen} />
          </Modal>
        </div>
      ) : null}
    </div>
  );
}
