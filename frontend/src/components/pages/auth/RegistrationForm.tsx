import { isAxiosError } from 'axios';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { yupResolver } from '@hookform/resolvers/yup';

import Layout from './Layout';
import Alert, { Status } from '../../Alert';
import { Button, OutlineButton } from '../../Buttons';
import HintText from '../../HintText';
import { InputField } from '../../FormFields';
import { User } from '../../../AuthContext';

import {
  registrationInitialValues as defaultValues,
  RegistrationFormData,
} from './initialValues';
import { registrationValidationSchema as validationSchema } from './validationSchema';

import api from '../../../api';

export const passwordHintText =
  'Your password must use at least 12 characters.';

export default function RegistrationForm() {
  const [status, setStatus] = useState<Status | null>(null);
  const [showPassword, toggleShowPassword] = useState(false);

  const methods = useForm<RegistrationFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });
  const {
    formState: { isSubmitting },
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<RegistrationFormData> = async (values) => {
    setStatus(null);
    try {
      const data = {
        first_name: values.firstName,
        last_name: values.lastName,
        email: values.email,
        password: values.password,
      };
      const response = await api.post<User>('/users', data);
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
      if (isAxiosError(err)) {
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
  };

  return (
    <Layout pageTitle="Create your account">
      <FormProvider {...methods}>
        <form
          className="grid grid-flow-row gap-4"
          onSubmit={handleSubmit(onSubmit)}
        >
          <div className="grid md:grid-cols-2 grid-cols-1 gap-4">
            <InputField label="First Name" name="firstName" />
            <InputField label="Last Name" name="lastName" />
          </div>
          <InputField label="Email" name="email" type="email" />
          <InputField
            label="Password"
            name="password"
            type={showPassword ? 'text' : 'password'}
          />
          <HintText>{passwordHintText}</HintText>
          <InputField
            label="Retype Password"
            name="passwordRetype"
            type={showPassword ? 'text' : 'password'}
          />
          <div className="flex items-center">
            <input
              id="default-checkbox"
              type="checkbox"
              className="w-4 h-4 text-slate-600 accent-slate-600 bg-gray-100 border-gray-300 rounded focus:ring-slate-500 focus:ring-2"
              onChange={(e) => toggleShowPassword(e.target.checked)}
            />
            <label
              htmlFor="default-checkbox"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Show password
            </label>
          </div>
          <Button type="submit" disabled={isSubmitting}>
            Create Account
          </Button>
        </form>
      </FormProvider>
      <div className="mt-4 grid grid-flow-row gap-4">
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
      </div>
    </Layout>
  );
}
