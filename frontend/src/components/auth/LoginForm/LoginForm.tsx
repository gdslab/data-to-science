import axios from 'axios';
import { Formik, Form } from 'formik';
import { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import Alert from '../../Alert';
import AuthContext from '../../../AuthContext';
import { CustomSubmitButton } from '../../forms/CustomButtons';
import CustomTextField from '../../forms/CustomTextField';

import initialValues from './initialValues';
import validationSchema from './validationSchema';

export default function LoginForm() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  return (
    <div className="h-full flex flex-wrap items-center justify-center">
      <div className="sm:w-full md:w-1/3 mx-4">
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
            <div>
              <span className="text-xl font-semibold">Login</span>
              <Form>
                <CustomTextField label="Email" name="email" type="email" />
                <CustomTextField label="Password" name="password" type="password" />
                <div className="mt-4">
                  <CustomSubmitButton disabled={isSubmitting}>Login</CustomSubmitButton>
                </div>
                {status && status.type && status.msg ? (
                  <div className="mt-4">
                    <Alert alertType={status.type}>{status.msg}</Alert>
                  </div>
                ) : null}
              </Form>
              <div className="block mt-4">
                Don't have an account yet?{' '}
                <Link to="/auth/register">Register here</Link>.
              </div>
            </div>
          )}
        </Formik>
      </div>
    </div>
  );
}
