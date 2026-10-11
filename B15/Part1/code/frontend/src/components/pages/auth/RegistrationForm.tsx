import { isAxiosError } from 'axios';
import clsx from 'clsx';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { Link } from 'react-router';
import { useEffect, useState } from 'react';
import { yupResolver } from '@hookform/resolvers/yup';

import Layout from './Layout';
import Alert, { Status } from '../../Alert';
import { Button, OutlineButton } from '../../Buttons';
import Checkbox from '../../Checkbox';
import HintText from '../../HintText';
import { InputField, TextAreaField } from '../../FormFields';
import TurnstileWidget from './TurnstileWidget';
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
  const [turnstileError, setTurnstileError] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileSiteKey, setTurnstileSiteKey] = useState<string>('');

  useEffect(() => {
    fetch('/config.json')
      .then((response) => response.json())
      .then((config) => {
        if (config.turnstileSiteKey) {
          setTurnstileSiteKey(config.turnstileSiteKey);
        }
      })
      .catch((error) => {
        console.error('Failed to load config.json:', error);
      });
  }, []);

  const methods = useForm<RegistrationFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });
  const {
    formState: { isSubmitting },
    handleSubmit,
    watch,
  } = methods;

  const handleTurnstileSuccess = (token: string) => {
    setTurnstileToken(token);
    setTurnstileError(false);
  };

  const handleTurnstileError = () => {
    setTurnstileToken(null);
    setTurnstileError(true);
  };

  const handleTurnstileExpired = () => {
    setTurnstileToken(null);
    setTurnstileError(true);
  };

  const currentIntent = watch('registrationIntent') || '';

  const onSubmit: SubmitHandler<RegistrationFormData> = async (values) => {
    setStatus(null);
    setTurnstileError(false);

    // If Turnstile is configured but no token available, show error
    if (turnstileSiteKey && !turnstileToken) {
      setTurnstileError(true);
      return;
    }

    try {
      const data = {
        first_name: values.firstName,
        last_name: values.lastName,
        email: values.email,
        password: values.password,
        registration_intent: values.registrationIntent,
        ...(turnstileToken && { turnstile_token: turnstileToken }),
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
      // Clear token on error so user can try again
      setTurnstileToken(null);

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
          <div className="grid lg:grid-cols-3 md:grid-cols-2 grid-cols-1 gap-4">
            <InputField label="First Name" name="firstName" />
            <InputField label="Last Name" name="lastName" />
            <InputField label="Email" name="email" type="email" />
          </div>
          <div>
            <TextAreaField
              label="How do you plan to use Data to Science? (optional)"
              name="registrationIntent"
              required={false}
              rows={2}
            />
            <span
              className={clsx('text-sm text-gray-400', {
                'text-red-500': currentIntent.length > 500,
              })}
            >
              {currentIntent.length.toLocaleString()} of 500 characters
            </span>
          </div>
          <HintText>{passwordHintText}</HintText>
          <div className="grid md:grid-cols-2 grid-cols-1 gap-4">
            <InputField
              label="Password"
              name="password"
              type={showPassword ? 'text' : 'password'}
            />
            <InputField
              label="Retype Password"
              name="passwordRetype"
              type={showPassword ? 'text' : 'password'}
            />
          </div>
          <div className="flex items-center">
            <Checkbox
              id="showpass-checkbox"
              checked={showPassword}
              onChange={(e) => toggleShowPassword(e.target.checked)}
            />
            <label
              htmlFor="showpass-checkbox"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Show password
            </label>
          </div>
          {turnstileSiteKey && (
            <TurnstileWidget
              siteKey={turnstileSiteKey}
              onSuccess={handleTurnstileSuccess}
              onError={handleTurnstileError}
              onExpire={handleTurnstileExpired}
            />
          )}
          {turnstileError && (
            <Alert alertType="error">
              Verification failed. Turnstile will retry automatically; if it
              still doesn't succeed, please reload the page and try again.
            </Alert>
          )}
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
