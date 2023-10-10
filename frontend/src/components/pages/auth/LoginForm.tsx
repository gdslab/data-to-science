import axios from 'axios';
import { Formik, Form } from 'formik';
import { useContext } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';

import Alert from '../../Alert';
import AuthContext from '../../../AuthContext';
import { Button, OutlineButton } from '../../Buttons';
import Card from '../../Card';
import { TextField } from '../../InputFields';

import Welcome from '../../pages/Welcome';

import { loginInitialValues as initialValues } from './initialValues';
import { loginValidationSchema as validationSchema } from './validationSchema';

export default function LoginForm() {
  const { login } = useContext(AuthContext);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  return (
    <div className="h-full bg-accent1">
      <div className="flex flex-wrap items-center justify-center">
        <div className="sm:w-full md:w-1/3 max-w-xl mx-4">
          <Welcome>Sign in to your account</Welcome>
          <Card>
            {searchParams.get('email_confirmed') === 'true' ? (
              <Alert alertType="success">Your email address has been confirmed.</Alert>
            ) : null}
            {searchParams.get('password_reset') === 'true' ? (
              <Alert alertType="success">Your password has been reset.</Alert>
            ) : null}
            <Formik
              initialValues={initialValues}
              validationSchema={validationSchema}
              onSubmit={async (values, { setSubmitting, setStatus }) => {
                setStatus(null);
                setSearchParams({});
                try {
                  const data = {
                    username: values.email,
                    password: values.password,
                  };
                  await login(data).then(() => navigate('/home'));
                } catch (err) {
                  if (axios.isAxiosError(err)) {
                    const errMsg = err.response?.data.detail;
                    if (err.response?.status === 401) {
                      setStatus({ type: 'warning', msg: errMsg });
                    } else if (err.response?.status === 403) {
                      if (errMsg.includes('email')) {
                        setStatus({
                          type: 'info',
                          msg: (
                            <span className="inline">
                              {errMsg}.{' '}
                              <button
                                className="font-semibold"
                                onClick={async (e) => {
                                  e.preventDefault();
                                  try {
                                    const response = await axios.get(
                                      '/api/v1/auth/request-email-confirmation',
                                      { params: { email: values.email } }
                                    );
                                    if (response)
                                      setStatus({
                                        type: 'info',
                                        msg: 'Email confirmation link sent',
                                      });
                                  } catch (err) {
                                    setStatus({
                                      type: 'error',
                                      msg: 'Unexpected error has occurred',
                                    });
                                  }
                                }}
                              >
                                Click here to request a new email confirmation link.
                              </button>
                            </span>
                          ),
                        });
                      } else {
                        setStatus({ type: 'info', msg: errMsg });
                      }
                    } else {
                      setStatus({ type: 'error', msg: errMsg });
                    }
                  } else {
                    setStatus(
                      typeof err === 'string'
                        ? { type: 'error', msg: err }
                        : { type: 'error', msg: 'Unexpected error has occurred' }
                    );
                  }
                }
                setSubmitting(false);
              }}
            >
              {({ isSubmitting, status }) => (
                <Form className="grid grid-flow-row gap-4">
                  <TextField label="Email" name="email" type="email" icon="email" />
                  <TextField
                    label="Password"
                    name="password"
                    type="password"
                    icon="password"
                  />
                  <div className="flex">
                    <Link className="shrink" to="/auth/recoverpassword">
                      <span className="block text-sm text-blue-500 font-bold pt-2 pb-1">
                        Forgot Password?
                      </span>
                    </Link>
                  </div>
                  <Button type="submit" disabled={isSubmitting}>
                    Login
                  </Button>
                  {status && status.type && status.msg ? (
                    <Alert alertType={status.type}>{status.msg}</Alert>
                  ) : null}
                  <div>
                    <span className="block text-sm text-slate-500 font-bold pt-2 pb-1">
                      Do not have an account?
                    </span>
                    <Link to="/auth/register">
                      <OutlineButton>Sign Up</OutlineButton>
                    </Link>
                  </div>
                </Form>
              )}
            </Formik>
          </Card>
        </div>
      </div>
    </div>
  );
}
