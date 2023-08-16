import axios from 'axios';
import { Link, Params, useLoaderData, useNavigate } from 'react-router-dom';

import { Button } from '../CustomButtons';
import DatasetList from '../DatasetList/DatasetList';

interface Project {
  id: string;
  title: string;
  description: string;
  planting_date: string;
  harvest_date: string;
  location_id: string;
  team_id: string;
}

export async function loader({ params }: { params: Params<string> }) {
  const project = await axios.get(`/api/v1/projects/${params.projectId}`);
  const datasets = await axios.get(`/api/v1/projects/${params.projectId}/datasets`);
  if (project && datasets) {
    return { project: project.data, datasets: datasets.data };
  } else {
    return null;
  }
}

function TableHeader({ columns }: { columns: string[] }) {
  return (
    <thead className="ltr:text-left rtl:text-right">
      <tr>
        {columns.map((col) => (
          <th
            key={col.replace(/\s+/g, '').toLowerCase()}
            className="whitespace-nowrap px-4 py-2 font-medium text-gray-900"
          >
            {col}
          </th>
        ))}
      </tr>
    </thead>
  );
}

function TableRow({ row }: { row: string[] }) {
  return (
    <tr>
      {row.map((value) => (
        <td
          key={value.replace(/\s+/g, '').toLowerCase()}
          className="whitespace-nowrap px-4 py-2 font-medium text-gray-900"
        >
          {value}
        </td>
      ))}
    </tr>
  );
}

function TableBody({ rows }: { rows: string[][] }) {
  return (
    <tbody className="divide-y divide-gray-200">
      {rows.map((row) => (
        <TableRow row={row} />
      ))}
    </tbody>
  );
}

export default function ProjectDetail() {
  const navigate = useNavigate();
  const project = useLoaderData() as Project;
  const datasets = [];

  return (
    <div className="">
      <div className="m-4">
        <div>
          <h2>{project.title}</h2>
          <span className="text-gray-600">{project.description}</span>
        </div>
      </div>
    </div>
  );
}
