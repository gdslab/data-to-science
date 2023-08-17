import axios from 'axios';
import { ReactNode } from 'react';
import { Link, Params, useLoaderData, useParams } from 'react-router-dom';

import { Button } from '../Buttons';

interface Project {
  id: string;
  title: string;
  description: string;
  planting_date: string;
  harvest_date: string;
  location_id: string;
  team_id: string;
}

interface Flight {
  id: string;
  acquisition_date: Date;
  altitude: number;
  side_overlap: number;
  forward_overlap: number;
  sensor: string;
  platform: string;
  project_id: string;
  pilot_id: string;
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

interface Action {
  key: string;
  label: string;
  url: string;
}

function TableBody({ actions, rows }: { actions?: Action[][]; rows: string[][] }) {
  return (
    <tbody className="divide-y divide-gray-200">
      {rows.map((row, i) => (
        <tr key={`row-${i}`}>
          {row.map((value, j) => (
            <td
              key={`cell-${i},${j}`}
              className="border border-slate-300 p-4 text-slate-500"
            >
              {value}
            </td>
          ))}
          {actions ? (
            <td className="border border-slate-300 p-4 text-slate-500">
              <div className="flex items-center justify-between gap-8">
                {actions[i].map((action) => (
                  <Link key={action.key} to={action.url}>
                    {action.label}
                  </Link>
                ))}
              </div>
            </td>
          ) : null}
        </tr>
      ))}
    </tbody>
  );
}

function TableHead({ columns }: { columns: string[] }) {
  return (
    <thead className="bg-slate-50">
      <tr>
        {columns.map((col) => (
          <th
            key={col.replace(/\s+/g, '').toLowerCase()}
            className="w-1/2 border border-slate-300 font-semibold p-4 text-lg text-slate-900 text-left"
          >
            {col}
          </th>
        ))}
      </tr>
    </thead>
  );
}

function Table({ children }: { children: ReactNode }) {
  return (
    <table className="table-auto border-separate border-spacing-1 w-full border border-slate-400">
      {children}
    </table>
  );
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
                    url: `/projects/${flight.id}/edit`,
                  },
                  {
                    key: `action-data-${i}`,
                    label: 'Raw Data',
                    url: `/projects/${flight.id}/data`,
                  },
                  {
                    key: `action-products-${i}`,
                    label: 'Data Product',
                    url: `/projects/${flight.id}/products`,
                  },
                  // {
                  //   key: `action-remove-${i}`,
                  //   label: 'Remove',
                  //   url: `/projects/${flight.id}/remove`,
                  // },
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
