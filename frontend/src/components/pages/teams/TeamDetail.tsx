import axios from 'axios';
import { Formik, Form } from 'formik';
import { useState } from 'react';
import { Params, useLoaderData, useNavigate, useRevalidator } from 'react-router-dom';
import * as Yup from 'yup';

import Alert from '../../Alert';
import { Button } from '../../Buttons';
import { Editing, EditField, TextField } from '../../InputFields';
import Modal from '../../Modal';
import TeamMemberList from './TeamMemberList';

import validationSchema from './validationSchema';

interface Team {
  id: string;
  is_owner: boolean;
  title: string;
  description: string;
}

export interface TeamMember {
  id: string;
  full_name: string;
  email: string;
}

export interface TeamData {
  team: Team;
  members: TeamMember[];
}

// fetches team details and team members prior to render
export async function loader({ params }: { params: Params<string> }) {
  try {
    const teamResponse = await axios.get(`/api/v1/teams/${params.teamId}`);
    const teamMembers = await axios.get(`/api/v1/teams/${params.teamId}/members`);
    if (teamResponse && teamMembers) {
      return { team: teamResponse.data, members: teamMembers.data };
    } else {
      return { team: null, members: [] };
    }
  } catch (err) {
    throw err;
  }
}

export default function TeamDetail() {
  const navigate = useNavigate();
  const revalidator = useRevalidator();
  const [open, setOpen] = useState(false);
  const teamData = useLoaderData() as TeamData;
  const [isEditing, setIsEditing] = useState<Editing>(null);

  return (
    <div>
      {teamData.team.is_owner ? (
        <Formik
          initialValues={{
            title: teamData.team.title,
            description: teamData.team.description,
          }}
          validationSchema={validationSchema}
          onSubmit={async (values) => {
            try {
              const response = await axios.put(
                `/api/v1/teams/${teamData.team.id}`,
                values
              );
              if (response) {
                revalidator.revalidate();
              }
              setIsEditing(null);
            } catch (err) {
              setIsEditing(null);
            }
          }}
        >
          {() => (
            <Form>
              <div className="grid rows-auto gap-2">
                <EditField
                  fieldName="title"
                  isEditing={isEditing}
                  setIsEditing={setIsEditing}
                >
                  {!isEditing || isEditing.field !== 'title' ? (
                    <h2 className="mb-0">{teamData.team.title}</h2>
                  ) : (
                    <TextField name="title" />
                  )}
                </EditField>
                <EditField
                  fieldName="description"
                  isEditing={isEditing}
                  setIsEditing={setIsEditing}
                >
                  {!isEditing || isEditing.field !== 'description' ? (
                    <span className="text-gray-600">{teamData.team.description}</span>
                  ) : (
                    <TextField name="description" />
                  )}
                </EditField>
              </div>
            </Form>
          )}
        </Formik>
      ) : (
        <div className="grid rows-auto gap-2">
          <h2 className="mb-0">{teamData.team.title}</h2>
          <span className="text-gray-600">{teamData.team.description}</span>
        </div>
      )}
      <hr className="mt-4 border-gray-700" />
      <div className="mt-9">
        <h2>{teamData.team.title} Members</h2>
        <TeamMemberList teamMembers={teamData.members} />
      </div>
      {teamData.team.is_owner ? (
        <div className="mt-4">
          <Formik
            initialValues={{ email: '' }}
            validationSchema={Yup.object({
              email: Yup.string().email('Invalid email address').required('Required'),
            })}
            onSubmit={async (values, { resetForm, setSubmitting, setStatus }) => {
              setStatus({ type: '', msg: '' });
              setSubmitting(true);
              try {
                const data = { email: values.email };
                const response = await axios.post(
                  `/api/v1/teams/${teamData.team.id}/members`,
                  data
                );
                if (response && response.status === 201) {
                  resetForm();
                  navigate('.');
                } else {
                  setStatus({ type: 'error', msg: 'Unable to add user' });
                  setSubmitting(false);
                }
              } catch (err) {
                if (axios.isAxiosError(err)) {
                  setStatus({ type: 'error', msg: err.response?.data.detail });
                } else {
                  setStatus({ type: 'error', msg: 'Unable to complete request' });
                }
                setSubmitting(false);
              }
            }}
          >
            {({ isSubmitting, setStatus, status }) => (
              <div>
                <Form className="grid grid-rows-3 gap-4">
                  <div className="flex flex-row items-end justify-between gap-4">
                    <div className="flex items-end gap-4">
                      <TextField type="email" label="Email" name="email" />
                      <Button type="submit" size="sm" disabled={isSubmitting}>
                        Add new member
                      </Button>
                    </div>
                    <div className="w-48">
                      <Button
                        type="button"
                        size="sm"
                        icon="trash"
                        onClick={() => setOpen(true)}
                      >
                        Delete team
                      </Button>
                      <Modal open={open} setOpen={setOpen}>
                        <ConfirmationPopup
                          setOpen={setOpen}
                          setStatus={setStatus}
                          teamId={teamData.team.id}
                        />
                      </Modal>
                    </div>
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
      ) : null}
    </div>
  );
}

function ConfirmationPopup({
  teamId,
  setOpen,
  setStatus,
}: {
  teamId: string;
  setOpen;
  setStatus;
}) {
  const navigate = useNavigate();
  return (
    <div className="rounded-lg bg-white p-8 shadow-2xl">
      <h2>Are you sure you want to delete this team?</h2>
      <p className="mt-2 text-sm text-gray-500">
        Deleting this team will cause all team members to immediately lose access to any
        projects, flights, and data associated with the team.
      </p>
      <div className="mt-8 flex justify-between">
        <Button type="button" size="sm" onClick={() => setOpen(false)}>
          No, keep team
        </Button>
        <Button
          type="submit"
          size="sm"
          icon="trash"
          onClick={async () => {
            try {
              const response = await axios.delete(`/api/v1/teams/${teamId}`);
              if (response) {
                setOpen(false);
                navigate('/teams', { state: { reload: true } });
              } else {
                setOpen(false);
                setStatus({ type: 'error', msg: 'Unable to delete team' });
              }
            } catch (err) {
              setOpen(false);
              setStatus({ type: 'error', msg: 'Unable to delete team' });
            }
          }}
        >
          Yes, delete team
        </Button>
      </div>
    </div>
  );
}
