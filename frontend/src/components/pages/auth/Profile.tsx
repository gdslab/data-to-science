import axios from 'axios';
import { Formik, Form } from 'formik';
import { useContext, useState } from 'react';
import seedrandom from 'seedrandom';
import { ChevronDownIcon, TrashIcon } from '@heroicons/react/24/outline';

import Alert from '../../Alert';
import AuthContext, { User } from '../../../AuthContext';
import { Button } from '../../Buttons';
import Card from '../../Card';
import HintText from '../../HintText';
import FileUpload from '../../FileUpload';
import { TextField } from '../../InputFields';
import { passwordHintText } from './RegistrationForm';

import { classNames } from '../../utils';
import {
  passwordChangeValidationSchema,
  profileValidationSchema,
} from './validationSchema';

const profileColors = [
  ['#355070', 'white'],
  ['#644F6D', 'white'],
  ['#C58794', 'black'],
  ['#E8787C', 'black'],
  ['#EAAC8B', 'black'],
  ['#074F57', 'white'],
  ['#065E6F', 'white'],
  ['#74A57F', 'black'],
  ['#9ECE9A', 'black'],
  ['#E4C5AF', 'black'],
];

/**
 * Randomly selects one of ten default profile background colors based on user's name.
 * @param {string} username User's first and last name
 * @returns {object} Style object for user's default profile background
 */
export function generateRandomProfileColor(username) {
  const seed = seedrandom(username);
  const colorIndex = Math.floor(seed.quick() * 10); // generate index between 0-9

  const profileColor = profileColors[colorIndex];
  return {
    backgroundColor: profileColor[0],
    color: profileColor[1],
    fontWeight: 550,
  };
}

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

function EditProfilePicture({ updateProfile }: { updateProfile: () => void }) {
  const [open, setOpen] = useState(false);
  const [menuVisibility, toggleMenuVisibility] = useState(false);
  const onSuccess = () => {
    updateProfile();
    setOpen(false);
    toggleMenuVisibility(false);
  };

  return (
    <>
      <div className="relative">
        <div className="inline-flex items-center overflow-hidden rounded-md border bg-white">
          <a
            href="#"
            className="border-e px-4 py-2 text-sm/none text-gray-600 hover:bg-gray-50 hover:text-gray-700 visited:text-gray-600"
            onClick={() => toggleMenuVisibility(!menuVisibility)}
          >
            Edit
          </a>

          <button
            className="h-full p-2 text-gray-600 hover:bg-gray-50 hover:text-gray-700"
            onClick={() => toggleMenuVisibility(!menuVisibility)}
          >
            <span className="sr-only">Menu</span>
            <ChevronDownIcon className="h-4 w-4" />
          </button>
        </div>

        <div
          className={classNames(
            menuVisibility ? 'display' : 'hidden',
            'absolute end-0 z-10 mt-2 w-56 rounded-md border border-gray-100 bg-white shadow-lg'
          )}
          role="menu"
        >
          <div className="p-2">
            <a
              href="#"
              className="block rounded-lg px-4 py-2 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700 visited:text-gray-500"
              role="menuitem"
              onClick={() => setOpen(true)}
            >
              Change profile picture
            </a>
            <button
              type="submit"
              className="flex w-full items-center gap-2 rounded-lg px-4 py-2 text-sm text-red-700 hover:bg-red-50"
              role="menuitem"
              onClick={async () => {
                try {
                  const response = await axios.delete(
                    `${import.meta.env.VITE_API_V1_STR}/users/profile`
                  );
                  if (response) {
                    toggleMenuVisibility(false);
                    updateProfile();
                  }
                } catch (err) {
                  console.log('unable to remove profile');
                }
              }}
            >
              <TrashIcon className="h-4 w-4" />
              Remove profile picture
            </button>
          </div>
        </div>
      </div>
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
    </>
  );
}

export default function Profile() {
  const { updateProfile, user } = useContext(AuthContext);

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
                  <div
                    className="flex items-center justify-center h-24 w-24 text-white text-4xl rounded-full"
                    style={generateRandomProfileColor(
                      `${user.first_name} ${user.last_name}`
                    )}
                  >
                    <span className="indent-[0.1em] tracking-widest">
                      {user.first_name[0] + user.last_name[0]}
                    </span>
                  </div>
                )}
                <EditProfilePicture updateProfile={updateProfile} />
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
