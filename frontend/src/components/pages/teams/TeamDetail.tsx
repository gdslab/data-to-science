import axios from 'axios';
import { Formik, Form } from 'formik';
import { useState } from 'react';
import { Params, useLoaderData, useNavigate, useRevalidator } from 'react-router-dom';
import * as Yup from 'yup';

import Alert from '../../Alert';
import { Button } from '../../Buttons';
import { Editing, EditTextField, TextField } from '../../InputFields';
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
  const teamData = useLoaderData() as TeamData;
  const [isEditing, setIsEditing] = useState<Editing>(null);
  return (
    <div>
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
              <EditTextField
                fieldName="title"
                isEditing={isEditing}
                setIsEditing={setIsEditing}
              >
                {!isEditing || isEditing.field !== 'title' ? (
                  <h2 className="mb-0">{teamData.team.title}</h2>
                ) : (
                  <TextField name="title" />
                )}
              </EditTextField>
              <EditTextField
                fieldName="description"
                isEditing={isEditing}
                setIsEditing={setIsEditing}
              >
                {!isEditing || isEditing.field !== 'description' ? (
                  <span className="text-gray-600">{teamData.team.description}</span>
                ) : (
                  <TextField name="description" />
                )}
              </EditTextField>
            </div>
          </Form>
        )}
      </Formik>
      <hr className="mt-4 border-gray-700" />
      <div className="mt-9">
        <h2>{teamData.team.title} Members</h2>
        <TeamMemberList teamMembers={teamData.members} />
      </div>
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
          {({ isSubmitting, status }) => (
            <div>
              <Form className="flex flex-col gap-4">
                <div>
                  <TextField type="email" label="Email" name="email" />
                </div>
                <div>
                  <Button type="submit" disabled={isSubmitting}>
                    Add new member
                  </Button>
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
    </div>
  );
}
