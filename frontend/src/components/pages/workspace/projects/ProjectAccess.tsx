import { AxiosResponse, isAxiosError } from 'axios';
import { useContext, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router';
import { CheckIcon } from '@heroicons/react/24/outline';

import { AlertBar } from '../../../Alert';
import { Button } from '../../../Buttons';
import { generateRandomProfileColor } from '../../auth/Profile';
import SearchUsers, { UserSearch } from '../../teams/SearchUsers';
import Table, { TableBody, TableHead } from '../../../Table';

import AuthContext from '../../../../AuthContext';
import { useProjectContext } from './ProjectContext';

import api from '../../../../api';
import { classNames } from '../../../utils';
import { sorter } from '../../../utils';

export interface ProjectMember {
  id: string;
  full_name: string;
  email: string;
  role: string;
  profile_url: string | null;
  member_id: string;
}

function AccessRoleRadioGroup({
  currentRole,
  memberId,
  uniqueID,
  updateProjectMemberRole,
}: {
  currentRole: string;
  memberId: string;
  uniqueID: string;
  updateProjectMemberRole: (projectMemberId: string, newRole: string) => void;
}) {
  const [error, setError] = useState('');
  const [role, updateRole] = useState(currentRole);

  const params = useParams();

  return (
    <div key={uniqueID} className="flex items-center justify-between gap-6">
      <fieldset className="flex flex-wrap gap-3">
        <legend className="sr-only">Role Level</legend>
        <select
          className="h-10 w-40 p-1.5 font-semibold text-zinc-600 text-center border-2 border-zinc-300 rounded-md bg-white disabled:opacity-50"
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
              const response: AxiosResponse<ProjectMember> = await api.put(
                `/projects/${params.projectId}/members/${memberId}`,
                payload
              );
              if (response) {
                updateProjectMemberRole(response.data.id, response.data.role);
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
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [searchResults, setSearchResults] = useState<UserSearch[]>([]);

  const { user } = useContext(AuthContext);
  const { projectMembers, projectMembersDispatch, projectRole } =
    useProjectContext();

  const navigate = useNavigate();
  const params = useParams();

  useEffect(() => {
    // Wait for projectRole to be loaded before checking access
    if (projectRole === undefined) {
      return;
    }

    // Limit access to project owners
    if (projectRole === 'owner') {
      setIsLoading(false);
    } else {
      navigate(-1);
    }
  }, [navigate, projectRole]);

  function updateProjectMemberRole(
    projectMemberId: string,
    newRole: string
  ): void {
    if (projectMembers) {
      projectMembersDispatch({
        type: 'set',
        payload: projectMembers.map((projectMember) => {
          if (projectMember.id === projectMemberId) {
            return { ...projectMember, role: newRole };
          } else {
            return projectMember;
          }
        }),
      });
    }
  }

  async function removeProjectMember(
    memberId: string,
    projectMembers: ProjectMember[]
  ) {
    try {
      const response = await api.delete(
        `/projects/${params.projectId}/members/${memberId}`
      );
      if (response) {
        projectMembersDispatch({
          type: 'set',
          payload: projectMembers.filter(({ id }) => id !== memberId),
        });
      }
    } catch (err) {
      if (isAxiosError(err)) {
        setError(err.response?.data.detail);
      } else {
        setError('Unable to process request');
      }
    }
  }

  if (isLoading) {
    return <div className="p-4">Loading...</div>;
  } else if (!projectMembers) {
    return <div className="p-4">Unable to find project members</div>;
  } else {
    return (
      <div className="flex flex-col p-4">
        <div>
          <h1>Manage Access</h1>
          <h2>Access Role Descriptions</h2>
          <div className="grid grid-rows-3 gap-1.5">
            <div className="grid grid-cols-6 gap-4">
              <span className="col-span-1 font-semibold text-slate-700">
                Owner:
              </span>
              <span className="col-span-5">
                Can create, update, view, and remove project data.
              </span>
            </div>
            <div className="grid grid-cols-6 gap-4">
              <span className="col-span-1 font-semibold text-slate-700">
                Manager:
              </span>
              <span className="col-span-5">
                Can create, update, and view project data.
              </span>
            </div>
            <div className="grid grid-cols-6 gap-4">
              <span className="col-span-1 font-semibold text-slate-700">
                Viewer:
              </span>
              <span className="col-span-5">Can view project data.</span>
            </div>
          </div>
        </div>
        <div className="overflow-x-auto">
          <div className="grow min-h-0 min-w-[1000px]">
            <Table>
              <TableHead
                align="left"
                columns={['Name', 'Email', 'Role', 'Actions']}
              />
              <div className="overflow-y-auto max-h-96 xl:max-h-[420px] 2xl:max-h-[512px]">
                <TableBody
                  align="left"
                  rows={projectMembers
                    .sort((a, b) => sorter(a.full_name, b.full_name))
                    .map(({ id, full_name, email, profile_url, role }) => ({
                      key: id,
                      values: [
                        profile_url ? (
                          <div className="flex items-center justify-start gap-4 whitespace-nowrap">
                            <img
                              key={profile_url
                                .split('/')
                                .slice(-1)[0]
                                .slice(0, -4)}
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
                              <span className="indent-[0.1em] tracking-widest">
                                {full_name[0]}
                                {full_name.split(' ').slice(-1)[0][0]}
                              </span>
                            </div>
                            <span>{full_name}</span>
                          </div>
                        ),
                        <span>{email}</span>,
                        <AccessRoleRadioGroup
                          currentRole={role}
                          memberId={id}
                          uniqueID={btoa(full_name)}
                          updateProjectMemberRole={updateProjectMemberRole}
                        />,
                        <button
                          className="text-sky-600"
                          type="button"
                          onClick={() =>
                            removeProjectMember(id, projectMembers)
                          }
                        >
                          Remove
                        </button>,
                      ],
                    }))}
                />
              </div>
            </Table>
          </div>
        </div>
        <div className="mt-4">
          <h3>Find new project members</h3>
          <div className="mb-4 grid grid-flow-row gap-4">
            <SearchUsers
              currentMembers={projectMembers}
              searchResults={searchResults}
              setSearchResults={setSearchResults}
              user={user}
            />
            {searchResults.length > 0 &&
            searchResults.filter((u) => u.checked).length > 0 ? (
              <Button
                size="sm"
                onClick={(e) => {
                  e.preventDefault();
                  const selectedMembers = searchResults.filter(
                    (u) => u.checked
                  );
                  if (selectedMembers.length > 0) {
                    api
                      .post(
                        `/projects/${params.projectId}/members/multi`,
                        selectedMembers.map(({ id }) => id)
                      )
                      .then((response: AxiosResponse<ProjectMember[]>) => {
                        projectMembersDispatch({
                          type: 'set',
                          payload: response.data,
                        });
                        setSearchResults([]);
                      })
                      .catch((err) => {
                        if (isAxiosError(err)) {
                          setError(err.response?.data.detail);
                        } else {
                          setError('Unable to process request');
                        }
                      });
                  }
                }}
              >
                Add Selected
              </Button>
            ) : null}
          </div>
        </div>
        {error ? <AlertBar alertType="error">{error}</AlertBar> : null}
      </div>
    );
  }
}
