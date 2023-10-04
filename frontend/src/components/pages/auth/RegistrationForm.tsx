import axios from 'axios';
import { Formik, Form } from 'formik';
import { Link } from 'react-router-dom';

import Alert from '../../Alert';
import { Button, OutlineButton } from '../../Buttons';
import Card from '../../Card';
import HintText from '../../HintText';
import { TextField } from '../../InputFields';

import Welcome from '../../pages/Welcome';

import { registrationInitialValues as initialValues } from './initialValues';
import { registrationValidationSchema as validationSchema } from './validationSchema';

export default function RegistrationForm() {
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
                  const response = await axios.post('/api/v1/users', data);
                  if (response) {
                    setStatus({
                      type: 'success',
                      msg: 'Registration complete. Please confirm your email address.',
                    });
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
                    Create Account
                  </Button>
                  <HintText>
                    New accounts will require email confirmation and manual approval
                    before use.
                  </HintText>
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
