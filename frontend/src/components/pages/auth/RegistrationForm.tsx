import axios from 'axios';
import { Formik, Form } from 'formik';
import { Link } from 'react-router-dom';
import { useState } from 'react';

import Alert from '../../Alert';
import { Button, OutlineButton } from '../../Buttons';
import Card from '../../Card';
import HintText from '../../HintText';
import { TextField } from '../../InputFields';

import Welcome from '../../pages/Welcome';

import { registrationInitialValues as initialValues } from './initialValues';
import { registrationValidationSchema as validationSchema } from './validationSchema';
import { User } from '../../../AuthContext';

export const passwordHintText = 'Your password must use at least 12 characters.';

export default function RegistrationForm() {
  const [showPassword, toggleShowPassword] = useState(false);
  return (
    <div className="h-full bg-accent1">
      <div className="flex flex-wrap items-center justify-center">
        <div className="sm:w-full md:w-1/3 max-w-xl mx-4">
          <Welcome>Create your account</Welcome>
          <Card>
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
                  const response = await axios.post<User>('/api/v1/users', data);
                  if (response) {
                    if (response.data.is_email_confirmed) {
                      setStatus({
                        type: 'success',
                        msg: `Registration complete. You are ready to log in to ${
                          import.meta.env.VITE_BRAND_FULL
                        }.`,
                      });
                    } else {
                      setStatus({
                        type: 'success',
                        msg: 'Registration complete. Please confirm your email address.',
                      });
                    }
                  } else {
                    setStatus({
                      type: 'warning',
                      msg: 'Unable to complete registration',
                    });
                  }
                } catch (err) {
                  if (axios.isAxiosError(err)) {
                    setStatus({
                      type: err.response?.status === 409 ? 'warning' : 'error',
                      msg: err.response?.data.detail,
                    });
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
              {({ isSubmitting, status }) => (
                <Form className="grid grid-flow-row gap-4">
                  <div className="grid md:grid-cols-2 grid-cols-1 gap-4">
                    <TextField label="First Name" name="firstName" />
                    <TextField label="Last Name" name="lastName" />
                  </div>
                  <TextField label="Email" name="email" type="email" />
                  <TextField
                    label="Password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                  />
                  <HintText>{passwordHintText}</HintText>
                  <div className="flex items-center">
                    <input
                      id="default-checkbox"
                      type="checkbox"
                      className="w-4 h-4 text-slate-600 accent-slate-600 bg-gray-100 border-gray-300 rounded focus:ring-slate-500 dark:focus:ring-slate-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                      onChange={(e) => toggleShowPassword(e.target.checked)}
                    />
                    <label
                      htmlFor="default-checkbox"
                      className="ms-2 text-sm font-medium text-gray-900 dark:text-gray-300"
                    >
                      Show password
                    </label>
                  </div>
                  <TextField
                    label="Retype Password"
                    name="passwordRetype"
                    type={showPassword ? 'text' : 'password'}
                  />
                  <Button type="submit" disabled={isSubmitting}>
                    Create Account
                  </Button>
                  {status && status.type && status.msg ? (
                    <Alert alertType={status.type}>{status.msg}</Alert>
                  ) : null}
                  <div>
                    <span className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                      Already have an account?
                    </span>
                    <Link to="/auth/login">
                      <OutlineButton>Login</OutlineButton>
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
