import axios from 'axios';
import { Formik, Form } from 'formik';
import { useContext, useState } from 'react';
import { UserCircleIcon } from '@heroicons/react/24/outline';

import Alert from '../../Alert';
import AuthContext, { User } from '../../../AuthContext';
import { Button } from '../../Buttons';
import Card from '../../Card';
import HintText from '../../HintText';
import FileUpload from '../../FileUpload';
import { TextField } from '../../InputFields';

import { passwordHintText } from './RegistrationForm';
import {
  passwordChangeValidationSchema,
  profileValidationSchema,
} from './validationSchema';

function ChangePasswordForm() {
  return (
    <Formik
      initialValues={{ passwordCurrent: '', passwordNew: '', passwordNewRetype: '' }}
      validationSchema={passwordChangeValidationSchema}
      onSubmit={async (values, { setStatus }) => {
        setStatus(null);
        try {
          const data = {
            current_password: values.passwordCurrent,
            new_password: values.passwordNew,
          };
          const response = await axios.post(
            `${import.meta.env.VITE_API_V1_STR}/auth/change-password`,
            data,
            {
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
              withCredentials: true,
            }
          );
          if (response) {
            response.status === 200
              ? setStatus({ type: 'success', msg: 'Password changed' })
              : setStatus({ type: 'error', msg: 'Unable to change password' });
          }
        } catch (err) {
          if (axios.isAxiosError(err)) {
            setStatus({ type: 'error', msg: err.response?.data.detail });
          } else {
            setStatus({ type: 'error', msg: 'Unable to change password' });
          }
        }
      }}
    >
      {({ dirty, isSubmitting, status }) => (
        <Form className="grid gap-4">
          <HintText>{passwordHintText}</HintText>
          <TextField label="Current Password" name="passwordCurrent" type="password" />
          <TextField label="New Password" name="passwordNew" type="password" />
          <TextField
            label="Retype New Password"
            name="passwordNewRetype"
            type="password"
          />
          <Button type="submit" size="sm" disabled={!dirty}>
            {isSubmitting ? 'Processing...' : 'Change Password'}
          </Button>
          {status && status.type && status.msg ? (
            <Alert alertType={status.type}>{status.msg}</Alert>
          ) : null}
        </Form>
      )}
    </Formik>
  );
}

interface ProfileProps {
  updateProfile: () => void;
  user: User;
}

function ProfileForm({ updateProfile, user }: ProfileProps) {
  return (
    <Formik
      // enableReinitialize={true}
      initialValues={{ firstName: user.first_name, lastName: user.last_name }}
      validationSchema={profileValidationSchema}
      onSubmit={async (values, { setSubmitting, setStatus }) => {
        setStatus(null);
        try {
          const data = {
            first_name: values.firstName,
            last_name: values.lastName,
          };
          const response = await axios.put(
            `${import.meta.env.VITE_API_V1_STR}/users/${user.id}`,
            data
          );
          if (response) {
            if (response.status === 200) {
              updateProfile();
              setStatus({ type: 'success', msg: 'Profile updated' });
            } else {
              setStatus({ type: 'error', msg: 'Unable to update profile' });
            }
          }
        } catch (err) {
          if (axios.isAxiosError(err)) {
            setStatus({ type: 'error', msg: err.response?.data.detail });
          } else {
            setStatus({ type: 'error', msg: 'Unable to update profile' });
          }
        }
        setSubmitting(false);
      }}
    >
      {({ dirty, isSubmitting, status }) => (
        <Form className="grid gap-4">
          <div className="grid grid-cols-2 gap-4">
            <TextField label="First Name" name="firstName" required={false} />
            <TextField label="Last Name" name="lastName" required={false} />
          </div>
          <TextField label="Email" name="email" required={false} disabled={true} />
          <Button type="submit" size="sm" disabled={!dirty}>
            {isSubmitting ? 'Processing...' : 'Update'}
          </Button>
          {status && status.type && status.msg ? (
            <Alert alertType={status.type}>{status.msg}</Alert>
          ) : null}
        </Form>
      )}
    </Formik>
  );
}

export default function Profile() {
  const { updateProfile, user } = useContext(AuthContext);
  const [open, setOpen] = useState(false);

  const onSuccess = () => updateProfile();

  return (
    <div className="h-full flex justify-center bg-gradient-to-b from-primary from-20% to-slate-200 to-10%">
      <div className="mt-16 sm:w-full md:w-1/2 max-w-xl mx-4">
        <h1 className="text-white">Edit Profile</h1>
        <Card>
          {!user ? (
            <span>Unable to load user profile</span>
          ) : (
            <div>
              {/* profile column */}
              <div className="flex flex-col items-center gap-1.5">
                <span className="font-semibold">
                  {user.first_name} {user.last_name}
                </span>
                <HintText>{user.email}</HintText>
                {user.profile_url ? (
                  <img
                    key={user.profile_url.split('/').slice(-1)[0].slice(0, -4)}
                    className="h-24 w-24 rounded-full"
                    src={user.profile_url}
                  />
                ) : (
                  <div className="h-24 w-24 mt-4 bg-accent2 rounded-full">
                    <UserCircleIcon />
                  </div>
                )}
                <div className="mt-4">
                  <Button size="sm" onClick={() => setOpen(true)}>
                    Change Photo
                  </Button>
                  <FileUpload
                    endpoint={`${import.meta.env.VITE_API_V1_STR}/users/profile`}
                    open={open}
                    onSuccess={onSuccess}
                    restrictions={{
                      allowedFileTypes: ['.jpg', '.png'],
                      maxNumberOfFiles: 1,
                      minNumberOfFiles: 1,
                    }}
                    setOpen={setOpen}
                    uploadType="img"
                  />
                </div>
              </div>
              {/* form column */}
              <div className="grid gap-8">
                <ProfileForm updateProfile={updateProfile} user={user} />
                <ChangePasswordForm />
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
