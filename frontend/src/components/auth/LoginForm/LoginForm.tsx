import axios from 'axios';
import { Formik, Form } from 'formik';
import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';

import AuthContext from '../../../AuthContext';
import { CustomSubmitButton } from '../../forms/CustomButtons';
import CustomTextField from '../../forms/CustomTextField';

import initialValues from './initialValues';
import validationSchema from './validationSchema';

export default function LoginForm() {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  return (
    <div className="w-1/3">
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={async (values, { setSubmitting, setStatus }) => {
          setStatus('');
          try {
            const data = {
              username: values.email,
              password: values.password,
            };
            await login(data).then(() => navigate('/home'));
          } catch (err) {
            if (axios.isAxiosError(err)) {
              setStatus(err.response?.data.detail);
            } else {
              setStatus(typeof err === 'string' ? err : 'Unknown error');
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
              {status ? (
                <div style={{ marginTop: 15 }}>
                  <span style={{ color: 'red' }}>{status}</span>
                </div>
              ) : null}
            </Form>
          </div>
        )}
      </Formik>
    </div>
  );
}
