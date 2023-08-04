import axios from 'axios';
import { Formik, Form } from 'formik';
import { Link } from 'react-router-dom';

import Alert from '../../Alert';
import { CustomSubmitButton } from '../../forms/CustomButtons';
import CustomTextField from '../../forms/CustomTextField';

import initialValues from './initialValues';
import validationSchema from './validationSchema';

export default function RegistrationForm() {
  return (
    <div className="h-full flex flex-wrap items-center justify-center">
      <div className="sm:w-full md:w-1/3 mx-4">
        <Formik
          initialValues={initialValues}
          validationSchema={validationSchema}
          onSubmit={async (values, { setSubmitting, setStatus }) => {
            try {
              const data = {
                first_name: values.firstName,
                last_name: values.lastName,
                email: values.email,
                password: values.password,
              };
              const response = await axios.post('/api/v1/users/', data);
              if (response) {
                // do something
              } else {
                // do something
              }
            } catch (err) {
              if (axios.isAxiosError(err)) {
                setStatus({ type: 'error', msg: err.response?.data.detail });
              } else {
                setStatus({
                  type: 'error',
                  msg: 'Unable to register account at this time',
                });
              }
            }
            setSubmitting(false);
          }}
        >
          {({ values, isSubmitting, status }) => (
            <div>
              <span className="text-xl font-semibold">Create Account</span>
              <Form>
                <CustomTextField label="First name" name="firstName" />
                <CustomTextField label="Last name" name="lastName" />
                <CustomTextField label="Email" name="email" type="email" />
                <CustomTextField label="Password" name="password" type="password" />
                {values.password.length > 0 ? (
                  <CustomTextField
                    label="Retype password"
                    name="passwordRetype"
                    type="password"
                  />
                ) : null}
                <div className="mt-4">
                  New accounts will require email confirmation and manual approval
                  before use. Already have an account?{' '}
                  <Link to="/auth/login">Sign in here</Link>.
                </div>
                <div className="mt-4">
                  <CustomSubmitButton disabled={isSubmitting}>
                    Register
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
