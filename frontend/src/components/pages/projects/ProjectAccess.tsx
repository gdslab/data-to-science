import axios from 'axios';
import { Params, useLoaderData } from 'react-router-dom';

import Table, { TableBody, TableHead } from '../../Table';
import { AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';

interface ProjectMembers {
  id: string;
  full_name: string;
  email: string;
  role: string;
}

export async function loader({ params }: { params: Params<string> }) {
  const response = await axios.get(
    `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/members`
  );
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

export default function ProjectAccess() {
  const projectMembers = useLoaderData() as ProjectMembers[];

  return (
    <div className="p-4">
      <h1>Manage Access</h1>
      <Table height={96}>
        <TableHead columns={['Name', 'Email', 'Role', 'Actions']} />
        <TableBody
          rows={projectMembers.map(({ full_name, email, role }) => [
            <span>{full_name}</span>,
            <span>{email}</span>,
            <span>{role}</span>,
          ])}
          actions={projectMembers.map(({ id }) => [
            {
              key: `action-change-role-${id}`,
              icon: <AdjustmentsHorizontalIcon className="h-4 w-4" />,
              label: 'Change Role',
              url: '#',
            },
          ])}
        />
      </Table>
    </div>
  );
}
