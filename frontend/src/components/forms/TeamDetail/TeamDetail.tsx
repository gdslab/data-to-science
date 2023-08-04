import axios from 'axios';
import { Formik, Form } from 'formik';
import { useLoaderData } from 'react-router-dom';
import * as Yup from 'yup';

import Alert from '../../Alert';
import { CustomSubmitButton } from '../CustomButtons';
import CustomTextField from '../../forms/CustomTextField';
import TeamMemberList from '../TeamMemberList/TeamMemberList';

interface Team {
  id: string;
  title: string;
  description: string;
}

export default function TeamDetail() {
  const team = useLoaderData() as Team;
  return (
    <div>
      <div>
        <h2>{team.title}</h2>
        <span className="text-gray-600">{team.description}</span>
      </div>
      <hr className="mt-4 border-gray-700" />
      <div className="mt-9">
        <h2>{team.title} Members</h2>
        <TeamMemberList />
      </div>
      <div className="mt-4">
        <Formik
          initialValues={{ email: '' }}
          validationSchema={Yup.object({
            email: Yup.string().email('Invalid email address').required('Required'),
          })}
          onSubmit={async (values, { setSubmitting, setStatus }) => {
            setStatus({ type: '', msg: '' });
            setSubmitting(true);
            try {
              const data = { email: values.email };
              const response = await axios.post(
                `/api/v1/teams/${team.id}/members`,
                data
              );
              if (response) {
                setStatus({ type: 'success', msg: 'Successfully added to team' });
                setSubmitting(false);
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
                  <CustomTextField type="email" label="Email" name="email" />
                </div>
                <div className="flex-none w-1/3">
                  <CustomSubmitButton disabled={isSubmitting}>
                    Add new member
                  </CustomSubmitButton>
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
