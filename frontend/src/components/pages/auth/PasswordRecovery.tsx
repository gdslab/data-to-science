import axios from 'axios';
import { Form, Formik } from 'formik';

import Alert from '../../Alert';
import { Button } from '../../Buttons';
import Card from '../../Card';
import { TextField } from '../../InputFields';
import Welcome from '../Welcome';

import { recoveryInitialValues as initialValues } from './initialValues';
import { recoveryValidationSchema as validationSchema } from './validationSchema';
import HintText from '../../HintText';

export default function PasswordRecovery() {
  return (
    <div className="h-full bg-accent1">
      <div className="flex flex-wrap items-center justify-center">
        <div className="sm:w-full md:w-1/3 max-w-xl mx-4">
          <Welcome>Password Recovery Request</Welcome>
          <Card>
            <Formik
              initialValues={initialValues}
              validationSchema={validationSchema}
              onSubmit={async (values, { setSubmitting, setStatus }) => {
                setStatus(null);
                setSubmitting(true);
                try {
                  const data = { email: values.email };
                  const response = await axios.get('/api/v1/auth/reset-password', {
                    params: data,
                  });
                  if (response) {
                    setStatus({
                      type: 'success',
                      msg: 'Password recovery email sent',
                    });
                    setSubmitting(false);
                  } else {
                    setStatus({
                      type: 'error',
                      msg: 'Unable to send password recovery email',
                    });
                    setSubmitting(false);
                  }
                } catch (err) {
                  setStatus({
                    type: 'error',
                    msg: 'Unable to send password recovery email',
                  });
                  setSubmitting(false);
                }
              }}
            >
              {({ isSubmitting, status }) => (
                <Form className="grid grid-flow-row gap-4">
                  <HintText>
                    Enter the email you used to sign up on{' '}
                    {import.meta.env.VITE_BRAND_FULL}. A one-time password reset link
                    will be sent to the address. The link will expire in 1 hour. Return
                    here to request a new link if needed.
                  </HintText>
                  <TextField label="Email" name="email" type="email" icon="email" />
                  <Button type="submit" disabled={isSubmitting}>
                    Send Reset Email
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
