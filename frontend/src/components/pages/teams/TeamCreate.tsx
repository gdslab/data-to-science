import axios from 'axios';
import { Form, Formik } from 'formik';
import { useContext, useEffect, useState } from 'react';
import { Link, useLoaderData, useNavigate, useRevalidator } from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';

import Alert from '../../Alert';
import AuthContext, { User } from '../../../AuthContext';
import { Button, OutlineButton } from '../../Buttons';
import Card from '../../Card';
import { Project } from '../projects/ProjectList';
import { SelectField, TextField } from '../../InputFields';

import initialValues from './initialValues';
import validationSchema from './validationSchema';

interface UserSearch extends User {
  checked: boolean;
}

interface TeamMember {
  id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
}

function SearchUsersBar({
  setSearchResults,
  user,
}: {
  setSearchResults: React.Dispatch<React.SetStateAction<UserSearch[]>>;
  user: User | null;
}) {
  const [searchValue, setSearchValue] = useState('');

  function updateSearchValue(e) {
    setSearchValue(e.target.value);
  }

  async function searchUsers() {
    try {
      const response = await axios.get('/api/v1/users', { params: { q: searchValue } });
      if (response) {
        const users = response.data
          .filter((u) => u.id !== user?.id)
          .map((u) => ({ ...u, checked: false }));
        setSearchResults(users);
      }
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="relative">
      <label htmlFor="Search" className="sr-only">
        {' '}
        Search{' '}
      </label>

      <input
        type="text"
        id="Search"
        placeholder="Search for users by name"
        className="w-full rounded-md border-gray-200 px-4 py-2.5 pe-10 shadow-sm sm:text-sm"
        value={searchValue}
        onChange={updateSearchValue}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            searchUsers();
            setSearchValue('');
          }
        }}
      />

      <span className="absolute inset-y-0 end-0 grid w-10 place-content-center">
        <button
          type="button"
          className="text-gray-600 hover:text-gray-700"
          onClick={() => {
            searchUsers();
            setSearchValue('');
          }}
        >
          <span className="sr-only">Search</span>

          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="1.5"
            stroke="currentColor"
            className="h-4 w-4"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
            />
          </svg>
        </button>
      </span>
    </div>
  );
}

export default function TeamCreate() {
  const { user } = useContext(AuthContext);
  const projects = useLoaderData() as Project[];
  const navigate = useNavigate();
  const revalidator = useRevalidator();
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [searchResults, setSearchResults] = useState<UserSearch[]>([]);

  useEffect(() => {
    if (user && teamMembers.length === 0) addTeamMember([user]);
  }, []);

  function addTeamMember(teamMember) {
    const uniqueIds = teamMembers.map((tm) => tm.id);
    const newTeamMembers = teamMember.filter((tm) => uniqueIds.indexOf(tm.id) === -1);

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
              const response = await axios.post('/api/v1/teams', data);
              if (response) {
                revalidator.revalidate();
                resetForm();
                navigate(`/teams/${response.data.id}`);
              } else {
                setStatus({ type: 'error', msg: 'Unable to create team' });
              }
            } catch (err) {
              console.log(err);
              if (axios.isAxiosError(err)) {
                setStatus({ type: 'error', msg: err.response?.data.detail });
              } else {
                setStatus({ type: 'error', msg: 'Unexpected error has occurred' });
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
                                <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                              </button>
                            ) : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mb-4">
                  <SearchUsersBar setSearchResults={setSearchResults} user={user} />
                </div>
                {searchResults && searchResults.length > 0 ? (
                  <div>
                    <span className="text-slate-600 font-bold">Search Results</span>
                    <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
                      <thead className="text-left">
                        <tr>
                          <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                            Name
                          </th>
                          <th>
                            <span
                              className="text-accent"
                              onClick={() => {
                                const updatedSearchResults = searchResults.map(
                                  (user) => {
                                    return { ...user, checked: true };
                                  }
                                );
                                setSearchResults(updatedSearchResults);
                              }}
                            >
                              Select All
                            </span>
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {searchResults.map((user) => (
                          <tr key={user.id} className="odd:bg-gray-50">
                            <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                              {user.first_name} {user.last_name}
                            </td>
                            <td className="text-center">
                              <label
                                htmlFor="AcceptConditions"
                                className="relative h-8 w-14 cursor-pointer"
                              >
                                <input
                                  id={`${user.id}-search-checkbox`}
                                  type="checkbox"
                                  value={user.id}
                                  checked={user.checked}
                                  className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                                  onChange={(e) => {
                                    const updatedSearchResults = searchResults.map(
                                      (user) => {
                                        if (user.id === e.target.value)
                                          return { ...user, checked: !user.checked };
                                        return user;
                                      }
                                    );
                                    setSearchResults(updatedSearchResults);
                                  }}
                                />
                              </label>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
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
                ) : null}
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
