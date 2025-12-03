import { isAxiosError } from 'axios';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router';
import { yupResolver } from '@hookform/resolvers/yup';

import Alert, { Status } from '../../Alert';
import { Button } from '../../Buttons';
import { InputField } from '../../FormFields';
import Layout from './Layout';

import {
  resetInitialValues as defaultValues,
  ResetFormData,
} from './initialValues';
import { resetValidationSchema as validationSchema } from './validationSchema';

import api from '../../../api';

export default function PasswordResetForm() {
  const [status, setStatus] = useState<Status | null>(null);
  const navigate = useNavigate();
  const [searchParams, _] = useSearchParams();

  useEffect(() => {
    if (!searchParams.has('token')) {
      navigate('/auth/recoverpassword');
    }
  }, []);

  const methods = useForm<ResetFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });
  const {
    formState: { isSubmitting },
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<ResetFormData> = async (values) => {
    setStatus(null);
    try {
      const data = {
        password: values.password,
        token: searchParams.get('token'),
      };
      const response = await api.post('/auth/reset-password', data);
      if (response) {
        navigate('/auth/login?password_reset=true');
      } else {
        setStatus({ type: 'error', msg: 'Unable to reset password' });
      }
    } catch (err) {
      if (isAxiosError(err)) {
        setStatus({ type: 'error', msg: err.response?.data.detail });
      } else {
        setStatus({ type: 'error', msg: 'Unable to reset password' });
      }
    }
  };

  if (!searchParams.has('token')) {
    return null;
  } else {
    return (
      <Layout pageTitle="Password Reset Form">
        <FormProvider {...methods}>
          <form
            className="grid grid-flow-row gap-4"
            onSubmit={handleSubmit(onSubmit)}
          >
            <InputField label="New Password" name="password" type="password" />
            <InputField
              label="Retype Password"
              name="passwordRetype"
              type="password"
            />
            <Button type="submit" disabled={isSubmitting}>
              Reset Password
            </Button>
            {status && status.type && status.msg ? (
              <Alert alertType={status.type}>{status.msg}</Alert>
            ) : null}
          </form>
        </FormProvider>
      </Layout>
    );
  }
}
