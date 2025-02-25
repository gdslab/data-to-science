import { AxiosResponse, isAxiosError } from 'axios';
import { Form, Formik } from 'formik';
import { useContext, useEffect, useState } from 'react';
import {
  Link,
  useLoaderData,
  useNavigate,
  useRevalidator,
} from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';

import Alert from '../../Alert';
import AuthContext from '../../../AuthContext';
import { Button, OutlineButton } from '../../Buttons';
import Card from '../../Card';
import { Project } from '../workspace/projects/ProjectList';
import { SelectField, TextField } from '../../InputFields';
import SearchUsers, { UserSearch } from './SearchUsers';

import initialValues from './initialValues';
import validationSchema from './validationSchema';

import api from '../../../api';

export async function loader() {
  const response: AxiosResponse<Project[]> = await api.get('/projects');
  if (response) {
    return response.data.filter(
      ({ role }) => role === 'owner' || role === 'manager'
    );
  } else {
    return [];
  }
}

export default function TeamCreate() {
  const { user } = useContext(AuthContext);
  const projects = useLoaderData() as Project[];
  const navigate = useNavigate();
  const revalidator = useRevalidator();

  const [teamMembers, setTeamMembers] = useState<UserSearch[]>([]);
  const [searchResults, setSearchResults] = useState<UserSearch[]>([]);

  useEffect(() => {
    if (user && teamMembers.length === 0) addTeamMember([user]);
  }, []);

  function addTeamMember(teamMember) {
    const uniqueIds = teamMembers.map((tm) => tm.id);
    const newTeamMembers = teamMember.filter(
      (tm) => uniqueIds.indexOf(tm.id) === -1
    );

    setTeamMembers([...teamMembers, ...newTeamMembers]);
    setSearchResults([]);
  }

  function removeTeamMember(teamMemberId) {
    setTeamMembers(teamMembers.filter((tm) => tm.id !== teamMemberId));
  }

  return (
    <Card title="Create a New Team">
      <div className="">
        <Formik
          initialValues={initialValues}
          validationSchema={validationSchema}
          onSubmit={async (values, { resetForm, setSubmitting, setStatus }) => {
            setStatus(null);
            try {
              const data = {
                title: values.title,
                description: values.description,
                new_members: teamMembers.map((tm) => tm.id),
                project: values.project,
              };
              const response = await api.post('/teams', data);
              if (response) {
                revalidator.revalidate();
                resetForm();
                navigate(`/teams/${response.data.id}`);
              } else {
                setStatus({ type: 'error', msg: 'Unable to create team' });
              }
            } catch (err) {
              if (isAxiosError(err)) {
                setStatus({ type: 'error', msg: err.response?.data.detail });
              } else {
                setStatus({
                  type: 'error',
                  msg: 'Unexpected error has occurred',
                });
              }
            }
            setSubmitting(false);
          }}
        >
          {({ isSubmitting, status }) => (
            <div>
              <Form>
                <div className="mb-4">
                  <TextField
                    altLabel={true}
                    label="What's the name of your new team?"
                    name="title"
                  />
                </div>
                <div className="mb-4">
                  <TextField
                    altLabel={true}
                    label="What is your team about? (Optional)"
                    name="description"
                  />
                </div>
                <div className="mb-4">
                  <span className="block font-bold pt-2 pb-1">
                    Who will be your team member?
                  </span>
                  <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
                    <thead className="text-left">
                      <tr>
                        <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                          Name
                        </th>
                        <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                          Email
                        </th>
                        <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                          Role
                        </th>
                        <th>Action</th>
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-gray-200">
                      {teamMembers.map((teamMember) => (
                        <tr key={teamMember.id} className="odd:bg-gray-50">
                          <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                            {teamMember.first_name} {teamMember.last_name}
                          </td>
                          <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                            {teamMember.email}
                          </td>
                          <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                            {user && user.email === teamMember.email
                              ? 'Owner'
                              : 'Member'}
                          </td>
                          <td className="text-center">
                            {user && teamMember.email !== user.email ? (
                              <button
                                type="button"
                                onClick={() => removeTeamMember(teamMember.id)}
                              >
                                <XMarkIcon
                                  className="h-6 w-6"
                                  aria-hidden="true"
                                />
                              </button>
                            ) : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mb-4 grid grid-flow-row gap-4">
                  <SearchUsers
                    currentMembers={teamMembers}
                    searchResults={searchResults}
                    setSearchResults={setSearchResults}
                    user={user}
                  />
                  <Button
                    size="sm"
                    onClick={(e) => {
                      e.preventDefault();
                      addTeamMember(searchResults.filter((u) => u.checked));
                    }}
                  >
                    Add Selected
                  </Button>
                </div>
                {projects && projects.length > 0 ? (
                  <div>
                    <SelectField
                      altLabel={true}
                      name="project"
                      label="Assign a Project (Optional)"
                      options={projects
                        .map((project) => ({
                          value: project.id,
                          label: project.title,
                        }))
                        .concat([{ value: '', label: 'No project' }])}
                    ></SelectField>
                  </div>
                ) : null}
                <div className="flex items-center justify-around mt-4">
                  <Button type="submit" disabled={isSubmitting}>
                    Done
                  </Button>
                  <Link to="/teams">
                    <OutlineButton>Cancel</OutlineButton>
                  </Link>
                </div>
                {status && status.type && status.msg ? (
                  <div className="mt-4">
                    <Alert alertType={status.type}>{status.msg}</Alert>
                  </div>
                ) : null}
              </Form>
            </div>
          )}
        </Formik>
      </div>
    </Card>
  );
}
