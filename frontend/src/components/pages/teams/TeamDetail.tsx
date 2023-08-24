import axios from 'axios';
import { Formik, Form } from 'formik';
import { Params, useLoaderData, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import Alert from '../../Alert';
import { Button } from '../../Buttons';
import { TextField } from '../../InputFields';
import TeamMemberList from './TeamMemberList';

interface Team {
  id: string;
  title: string;
  description: string;
}

export interface TeamMember {
  id: string;
  full_name: string;
  email: string;
}

interface TeamData {
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
  const teamData = useLoaderData() as TeamData;
  return (
    <div>
      <div>
        <h2>{teamData.team.title}</h2>
        <span className="text-gray-600">{teamData.team.description}</span>
      </div>
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
                <div className="flex-none w-1/3">
                  <TextField type="email" label="Email" name="email" />
                </div>
                <div className="flex-none w-1/3">
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
