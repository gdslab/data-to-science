import axios from 'axios';
import { Formik, Form } from 'formik';
import { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import Alert from '../../Alert';
import AuthContext from '../../../AuthContext';
import { Button, OutlineButton } from '../../forms/CustomButtons';
import Card from '../../Card';
import CustomTextField from '../../forms/CustomTextField';
import HintText from '../../HintText';
import Welcome from '../../Welcome';

import initialValues from './initialValues';
import validationSchema from './validationSchema';

export default function LoginForm() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  return (
    <div className="h-full flex flex-wrap items-center justify-center bg-accent1">
      <div className="sm:w-full md:w-1/3 max-w-xl mx-4">
        <Welcome>Sign in to your account</Welcome>
        <Card>
          <Formik
            initialValues={initialValues}
            validationSchema={validationSchema}
            onSubmit={async (values, { setSubmitting, setStatus }) => {
              setStatus(null);
              try {
                const data = {
                  username: values.email,
                  password: values.password,
                };
                await login(data).then(() => navigate('/home'));
              } catch (err) {
                if (axios.isAxiosError(err)) {
                  const errMsg = err.response?.data.detail;
                  if (errMsg === 'Invalid credentials') {
                    setStatus({ type: 'warning', msg: errMsg });
                  } else if (errMsg === 'Account needs approval') {
                    setStatus({ type: 'info', msg: errMsg });
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
              <Form className="flex flex-col items-center gap-4">
                <div className="w-full">
                  <CustomTextField
                    label="Email"
                    name="email"
                    type="email"
                    icon="email"
                  />
                </div>
                <div className="w-full">
                  <CustomTextField
                    label="Password"
                    name="password"
                    type="password"
                    icon="password"
                  />
                </div>
                <div className="self-end">
                  <Link to="/auth/recoverpassword">
                    <HintText>Forgot Password?</HintText>
                  </Link>
                </div>
                <div className="w-full">
                  <Button type="submit" disabled={isSubmitting}>
                    Login
                  </Button>
                </div>
                {status && status.type && status.msg ? (
                  <div className="w-full">
                    <Alert alertType={status.type}>{status.msg}</Alert>
                  </div>
                ) : null}
                <div className="w-full">
                  <span className="block text-sm text-gray-400 font-bold pt-2 pb-1">
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
  );
}
