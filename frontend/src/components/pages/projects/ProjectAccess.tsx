import axios, { isAxiosError } from 'axios';
import { useContext, useEffect, useState } from 'react';
import {
  Params,
  useLoaderData,
  useParams,
  useNavigate,
  useRevalidator,
} from 'react-router-dom';

import { AlertBar } from '../../Alert';
import Table, { TableBody, TableHead } from '../../Table';
import { CheckIcon } from '@heroicons/react/24/outline';

import { generateRandomProfileColor } from '../auth/Profile';
import { classNames } from '../../utils';
import { sorter } from '../../utils';
import AuthContext from '../../../AuthContext';

interface ProjectMembers {
  id: string;
  full_name: string;
  email: string;
  role: string;
  profile_url: string | null;
  member_id: string;
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

function AccessRoleRadioGroup({
  currentRole,
  memberId,
  uniqueID,
}: {
  currentRole: string;
  memberId: string;
  uniqueID: string;
}) {
  const [error, setError] = useState('');
  const [role, updateRole] = useState(currentRole);
  const params = useParams();
  const revalidator = useRevalidator();
  return (
    <div className="flex items-center justify-between gap-4">
      <fieldset key={uniqueID} className="flex flex-wrap gap-3">
        <legend className="sr-only">Role Level</legend>
        <select
          className="h-10 p-1.5 font-semibold text-zinc-600 text-center border-2 border-zinc-300 rounded-md bg-white disabled:opacity-50"
          aria-label="Select flight date"
          name={`roleChange-${uniqueID}`}
          value={role}
          onChange={(e) => {
            updateRole(e.target.value);
          }}
        >
          <option value="owner">Owner</option>
          <option value="manager">Manager</option>
          <option value="viewer">Viewer</option>
        </select>
      </fieldset>
      <button
        className={classNames(
          currentRole !== role ? '' : 'text-gray-300',
          'flex items-center gap-1.5'
        )}
        onClick={async (e) => {
          e.preventDefault();
          setError('');
          if (currentRole !== role) {
            try {
              const payload = { role: role };
              const response = await axios.put(
                `${import.meta.env.VITE_API_V1_STR}/projects/${
                  params.projectId
                }/members/${memberId}`,
                payload
              );
              if (response) {
                revalidator.revalidate();
              } else {
                alert('could not update user role');
              }
            } catch (err) {
              if (isAxiosError(err)) {
                setError(err.response?.data.detail);
              } else {
                setError('Unable to process request');
              }
            }
          }
        }}
      >
        <CheckIcon className="h-4 w-4" />
        <span>Save</span>
      </button>
      {error ? <AlertBar alertType="error">{error}</AlertBar> : null}
    </div>
  );
}

export default function ProjectAccess() {
  const [isLoading, setIsLoading] = useState(true);
  const projectMembers = useLoaderData() as ProjectMembers[];
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      const userProjectMember = projectMembers.filter(
        ({ member_id }) => member_id === user.id
      );
      if (userProjectMember.length > 0 && userProjectMember[0].role === 'owner') {
        setIsLoading(false);
      } else {
        navigate(-1);
      }
    } else {
      navigate(-1);
    }
  }, []);

  if (isLoading) {
    return <div className="p-4">Loading...</div>;
  } else {
    return (
      <div className="p-4">
        <h1>Manage Access</h1>
        <h2>Access Role Descriptions</h2>
        <div className="grid grid-rows-3 gap-1.5">
          <div className="grid grid-cols-6 gap-4">
            <span className="col-span-1 font-semibold text-slate-700">Owner:</span>
            <span className="col-span-5">
              Can create, update, view, and remove project data.
            </span>
          </div>
          <div className="grid grid-cols-6 gap-4">
            <span className="col-span-1 font-semibold text-slate-700">Manager:</span>
            <span className="col-span-5">
              Can create, update, and view project data.
            </span>
          </div>
          <div className="grid grid-cols-6 gap-4">
            <span className="col-span-1 font-semibold text-slate-700">Viewer:</span>
            <span className="col-span-5">Can view project data.</span>
          </div>
        </div>
        <Table height={96}>
          <TableHead align="left" columns={['Name', 'Email', 'Role']} />
          <TableBody
            align="left"
            rows={projectMembers
              .sort((a, b) => sorter(a.full_name, b.full_name))
              .map(({ id, full_name, email, profile_url, role }) => [
                profile_url ? (
                  <div className="flex items-center justify-start gap-4 whitespace-nowrap">
                    <img
                      key={profile_url.split('/').slice(-1)[0].slice(0, -4)}
                      className="h-8 w-8 rounded-full"
                      src={profile_url}
                    />
                    <span>{full_name}</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-start gap-4 whitespace-nowrap">
                    <div
                      className="flex items-center justify-center h-8 w-8 text-white text-sm rounded-full"
                      style={generateRandomProfileColor(full_name)}
                    >
                      {full_name[0]} {full_name.split(' ').slice(-1)[0][0]}
                    </div>
                    <span>{full_name}</span>
                  </div>
                ),
                <span>{email}</span>,
                <AccessRoleRadioGroup
                  currentRole={role}
                  memberId={id}
                  uniqueID={btoa(full_name)}
                />,
              ])}
          />
        </Table>
      </div>
    );
  }
}
