import { isAxiosError } from 'axios';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useEffect } from 'react';
import { yupResolver } from '@hookform/resolvers/yup';

import { Button, OutlineButton } from '../../Buttons';
import { InputField } from '../../FormFields';
import HintText from '../../HintText';
import { Status } from '../../Alert';
import { User } from '../../../AuthContext';

import api from '../../../api';
import { emailChangeValidationSchema } from './validationSchema';

interface ChangeEmailFormProps {
  setShowChangeEmailForm: React.Dispatch<React.SetStateAction<boolean>>;
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
  updateProfile: () => Promise<void>;
  user: User;
}

type ChangeEmailFormData = {
  currentPassword: string;
  newEmail: string;
};

export default function ChangeEmailForm({
  setShowChangeEmailForm,
  setStatus,
  updateProfile,
  user,
}: ChangeEmailFormProps) {
  useEffect(() => {
    setStatus(null);
  }, [setStatus]);

  const defaultValues = {
    currentPassword: '',
    newEmail: '',
  };

  const methods = useForm<ChangeEmailFormData>({
    defaultValues,
    resolver: yupResolver(emailChangeValidationSchema),
  });
  const {
    formState: { isDirty, isSubmitting },
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<ChangeEmailFormData> = async (values) => {
    setStatus(null);
    try {
      const data = {
        current_password: values.currentPassword,
        new_email: values.newEmail,
      };
      const response = await api.post('/auth/change-email', data, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        withCredentials: true,
      });
      if (response) {
        if (response.status === 200) {
          await updateProfile();
          const msg =
            response.data?.detail === 'email_changed'
              ? 'Your email address has been updated.'
              : 'A verification link has been sent to your new email address. Please check your inbox to confirm the change.';
          setStatus({ type: 'success', msg });
          setShowChangeEmailForm(false);
        } else {
          setStatus({ type: 'error', msg: 'Unable to change email' });
        }
      }
    } catch (err) {
      if (isAxiosError(err)) {
        setStatus({ type: 'error', msg: err.response?.data.detail });
      } else {
        setStatus({ type: 'error', msg: 'Unable to change email' });
      }
    }
  };

  return (
    <FormProvider {...methods}>
      <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
        <HintText>
          Enter your current password and new email address. A verification link
          will be sent to the new address.
        </HintText>
        {user.pending_email && (
          <HintText>
            A verification email was sent to{' '}
            <span className="font-semibold">{user.pending_email}</span>. Check
            your inbox to confirm.
          </HintText>
        )}
        <InputField
          label="Current Password"
          name="currentPassword"
          type="password"
        />
        <InputField label="New Email Address" name="newEmail" type="email" />
        <Button type="submit" size="sm" disabled={!isDirty}>
          {isSubmitting ? 'Processing...' : 'Change Email'}
        </Button>
        <OutlineButton
          type="button"
          size="sm"
          onClick={() => setShowChangeEmailForm(false)}
        >
          Cancel
        </OutlineButton>
      </form>
    </FormProvider>
  );
}
