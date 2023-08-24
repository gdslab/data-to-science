import axios from 'axios';
import { Formik, Form } from 'formik';
import { useNavigate } from 'react-router-dom';

import Alert from '../../Alert';
import { Button } from '../../Buttons';
import { TextField } from '../../InputFields';

import initialValues from './initialValues';
import validationSchema from './validationSchema';

export default function TeamForm() {
  const navigate = useNavigate();

  return (
    <div style={{ width: 450 }}>
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={async (values, { resetForm, setSubmitting, setStatus }) => {
          setStatus(null);
          try {
            const data = {
              title: values.title,
              description: values.description,
            };
            const response = await axios.post('/api/v1/teams', data);
            if (response) {
              navigate('/teams');
              resetForm();
            } else {
              setStatus({ type: 'error', msg: 'Unable to create team' });
            }
          } catch (err) {
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
            <h1>Create team</h1>
            <Form>
              <TextField label="Title" name="title" />
              <TextField label="Description" name="description" />
              <div className="mt-4">
                <Button type="submit" disabled={isSubmitting}>
                  Create team
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
  );
}
