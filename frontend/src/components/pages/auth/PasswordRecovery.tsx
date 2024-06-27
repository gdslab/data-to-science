import axios from 'axios';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useState } from 'react';
import { yupResolver } from '@hookform/resolvers/yup';

import Alert, { Status } from '../../Alert';
import { Button } from '../../Buttons';
import { InputField } from '../../FormFields';
import Layout from './Layout';

import {
  recoveryInitialValues as defaultValues,
  RecoveryFormData,
} from './initialValues';
import { recoveryValidationSchema as validationSchema } from './validationSchema';
import HintText from '../../HintText';

export default function PasswordRecovery() {
  const [status, setStatus] = useState<Status | null>(null);

  const methods = useForm<RecoveryFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });
  const {
    formState: { isSubmitting },
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<RecoveryFormData> = async (values) => {
    setStatus(null);
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
      } else {
        setStatus({
          type: 'error',
          msg: 'Unable to send password recovery email',
        });
      }
    } catch (err) {
      setStatus({
        type: 'error',
        msg: 'Unable to send password recovery email',
      });
    }
  };

  return (
    <Layout pageTitle="Password Recovery Request">
      <FormProvider {...methods}>
        <form className="grid grid-flow-row gap-4" onSubmit={handleSubmit(onSubmit)}>
          <HintText>
            Enter the email you used to sign up on {import.meta.env.VITE_BRAND_FULL}. A
            one-time password reset link will be sent to the address. The link will
            expire in 1 hour. Return here to request a new link if needed.
          </HintText>
          <InputField label="Email" name="email" type="email" />
          <Button type="submit" disabled={isSubmitting}>
            Send Reset Email
          </Button>
          {status && status.type && status.msg ? (
            <Alert alertType={status.type}>{status.msg}</Alert>
          ) : null}
        </form>
      </FormProvider>
    </Layout>
  );
}
