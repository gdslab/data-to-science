import axios from 'axios';
import { Form, Formik } from 'formik';
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import Alert from '../../Alert';
import { Button } from '../../Buttons';
import Card from '../../Card';
import { TextField } from '../../InputFields';
import Welcome from '../Welcome';

import { resetInitialValues as initialValues } from './initialValues';
import { resetValidationSchema as validationSchema } from './validationSchema';

export default function PasswordResetForm() {
  const navigate = useNavigate();
  const [searchParams, _] = useSearchParams();

  useEffect(() => {
    if (!searchParams.has('token')) {
      navigate('/auth/recoverpassword');
    }
  }, []);

  if (!searchParams.has('token')) {
    return null;
  } else {
    return (
      <div className="h-full bg-accent1">
        <div className="flex flex-wrap items-center justify-center">
          <div className="sm:w-full md:w-1/3 max-w-xl mx-4">
            <Welcome>Password Reset Form</Welcome>
            <Card>
              <Formik
                initialValues={initialValues}
                validationSchema={validationSchema}
                onSubmit={async (values, { setSubmitting, setStatus }) => {
                  setStatus(null);
                  setSubmitting(true);
                  try {
                    const data = {
                      password: values.password,
                      token: searchParams.get('token'),
                    };
                    const response = await axios.post(
                      '/api/v1/auth/reset-password',
                      data
                    );
                    if (response) {
                      setSubmitting(false);
                      navigate('/auth/login?password_reset=true');
                    } else {
                      setSubmitting(false);
                      setStatus({ type: 'error', msg: 'Unable to reset password' });
                    }
                  } catch (err) {
                    if (axios.isAxiosError(err)) {
                      setStatus({ type: 'error', msg: err.response?.data.detail });
                    } else {
                      setStatus({ type: 'error', msg: 'Unable to reset password' });
                    }
                    setSubmitting(false);
                  }
                }}
              >
                {({ isSubmitting, status }) => (
                  <Form className="grid grid-flow-row gap-4">
                    <TextField
                      label="New Password"
                      name="password"
                      type="password"
                      icon="password"
                    />
                    <TextField
                      label="Retype Password"
                      name="passwordRetype"
                      type="password"
                      icon="password"
                    />
                    <Button type="submit" disabled={isSubmitting}>
                      Reset Password
                    </Button>
                    {status && status.type && status.msg ? (
                      <Alert alertType={status.type}>{status.msg}</Alert>
                    ) : null}
                  </Form>
                )}
              </Formik>
            </Card>
          </div>
        </div>
      </div>
    );
  }
}
