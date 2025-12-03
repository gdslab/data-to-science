import { isAxiosError } from 'axios';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { Fragment, useContext, useState } from 'react';
import {
  Link,
  useLocation,
  useNavigate,
  useSearchParams,
} from 'react-router';
import { yupResolver } from '@hookform/resolvers/yup';

import Alert, { Status } from '../../Alert';
import AuthContext from '../../../AuthContext';
import { Button, OutlineButton } from '../../Buttons';
import { InputField } from '../../FormFields';
import Layout from './Layout';

import {
  loginInitialValues as defaultValues,
  LoginFormData,
} from './initialValues';
import { loginValidationSchema as validationSchema } from './validationSchema';

import api from '../../../api';

function SearchParamAlerts({
  searchParams,
}: {
  searchParams: URLSearchParams;
}) {
  return (
    <Fragment>
      {searchParams.get('email_confirmed') === 'true' && (
        <Alert alertType="success">
          Your email address has been confirmed.
        </Alert>
      )}
      {searchParams.get('password_reset') === 'true' && (
        <Alert alertType="success">Your password has been reset.</Alert>
      )}
    </Fragment>
  );
}

export default function LoginForm() {
  const [status, setStatus] = useState<Status | null>(null);
  const { login } = useContext(AuthContext);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();

  const methods = useForm<LoginFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });
  const {
    formState: { isSubmitting },
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<LoginFormData> = async (values) => {
    setStatus(null);
    setSearchParams({});
    try {
      const data = {
        username: values.email,
        password: values.password,
      };
      await login(data).then(() => {
        // Check if there's a redirect location from the navigation state
        const from = location.state?.from?.pathname || '/home';
        navigate(from, { replace: true });
      });
    } catch (err) {
      if (isAxiosError(err)) {
        const errMsg = err.response?.data.detail;
        if (err.response?.status === 401) {
          setStatus({ type: 'warning', msg: errMsg });
        } else if (err.response?.status === 403) {
          if (errMsg.includes('email')) {
            setStatus({
              type: 'info',
              msg: (
                <span className="inline">
                  {errMsg}.{' '}
                  <button
                    className="font-semibold"
                    onClick={async (e) => {
                      e.preventDefault();
                      try {
                        const response = await api.get(
                          '/auth/request-email-confirmation',
                          { params: { email: values.email } }
                        );
                        if (response)
                          setStatus({
                            type: 'info',
                            msg: 'Email confirmation link sent',
                          });
                      } catch (err) {
                        setStatus({
                          type: 'error',
                          msg: 'Unexpected error has occurred',
                        });
                      }
                    }}
                  >
                    Click here to request a new email confirmation link.
                  </button>
                </span>
              ),
            });
          } else {
            setStatus({ type: 'info', msg: errMsg });
          }
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
  };

  return (
    <Layout pageTitle="Sign in to your account">
      <SearchParamAlerts searchParams={searchParams} />
      <FormProvider {...methods}>
        <form
          className="grid grid-flow-row gap-4"
          onSubmit={handleSubmit(onSubmit)}
        >
          {/* Email input field */}
          <InputField label="Email" name="email" />
          {/* Password input field */}
          <InputField label="Password" name="password" type="password" />
          {/* Forgot password link */}
          <Link className="shrink" to="/auth/recoverpassword">
            <span className="block text-sm text-blue-500 font-bold pt-2 pb-1">
              Forgot Password?
            </span>
          </Link>
          {/* Login submission button */}
          <Button type="submit" disabled={isSubmitting}>
            Login
          </Button>
        </form>
      </FormProvider>
      <div className="mt-4 grid grid-flow-row gap-4">
        {/* Display any error messages from backend API */}
        {status && status.type && status.msg && (
          <Alert alertType={status.type}>{status.msg}</Alert>
        )}
        {/* Sign up link */}
        <div>
          <span className="block text-sm text-slate-500 font-bold pt-2 pb-1">
            Do not have an account?
          </span>
          <Link to="/auth/register">
            <OutlineButton>Sign Up</OutlineButton>
          </Link>
        </div>
      </div>
    </Layout>
  );
}
