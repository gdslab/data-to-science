import axios, { AxiosResponse } from 'axios';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { Fragment, useContext, useEffect, useState } from 'react';
import seedrandom from 'seedrandom';
import {
  ChevronDownIcon,
  DocumentDuplicateIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { yupResolver } from '@hookform/resolvers/yup';

import ProfilePictureUpload from './ProfilePictureUpload';
import { passwordHintText } from './RegistrationForm';
import Alert, { Status } from '../../Alert';
import { Button, OutlineButton } from '../../Buttons';
import Card from '../../Card';
import { InputField } from '../../FormFields';
import HintText from '../../HintText';
import AuthContext, { User } from '../../../AuthContext';

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

interface Profile {
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
}

interface ChangePasswordForm extends Profile {
  setShowChangePasswordForm: React.Dispatch<React.SetStateAction<boolean>>;
}

function ChangePasswordForm({
  setShowChangePasswordForm,
  setStatus,
}: ChangePasswordForm) {
  useEffect(() => {
    setStatus(null);
  }, []);

  const defaultValues = {
    passwordCurrent: '',
    passwordNew: '',
    passwordNewRetype: '',
  };

  type ChangePasswordFormData = {
    passwordCurrent: string;
    passwordNew: string;
    passwordNewRetype: string;
  };

  const methods = useForm<ChangePasswordFormData>({
    defaultValues,
    resolver: yupResolver(passwordChangeValidationSchema),
  });
  const {
    formState: { isDirty, isSubmitting },
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<ChangePasswordFormData> = async (values) => {
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
        if (response.status === 200) {
          setStatus({ type: 'success', msg: 'Password changed' });
          setShowChangePasswordForm(false);
        } else {
          setStatus({ type: 'error', msg: 'Unable to change password' });
        }
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setStatus({ type: 'error', msg: err.response?.data.detail });
      } else {
        setStatus({ type: 'error', msg: 'Unable to change password' });
      }
    }
  };

  return (
    <FormProvider {...methods}>
      <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
        <HintText>{passwordHintText}</HintText>
        <InputField label="Current Password" name="passwordCurrent" type="password" />
        <InputField label="New Password" name="passwordNew" type="password" />
        <InputField
          label="Retype New Password"
          name="passwordNewRetype"
          type="password"
        />
        <Button type="submit" size="sm" disabled={!isDirty}>
          {isSubmitting ? 'Processing...' : 'Change Password'}
        </Button>
        <OutlineButton
          type="button"
          size="sm"
          onClick={() => setShowChangePasswordForm(false)}
        >
          Cancel
        </OutlineButton>
      </form>
    </FormProvider>
  );
}

interface ProfileProps extends Profile {
  updateProfile: () => void;
  user: User;
}

function ProfileForm({ setStatus, updateProfile, user }: ProfileProps) {
  const defaultValues = {
    firstName: user.first_name,
    lastName: user.last_name,
  };
  type ProfileFormData = {
    firstName: string;
    lastName: string;
  };

  const methods = useForm<ProfileFormData>({
    defaultValues,
    resolver: yupResolver(profileValidationSchema),
  });
  const {
    formState: { isDirty, isSubmitting },
    handleSubmit,
    reset,
  } = methods;

  const onSubmit: SubmitHandler<ProfileFormData> = async (values) => {
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
          reset(values);
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
  };

  return (
    <FormProvider {...methods}>
      <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
        <div className="flex flex-row justify-between gap-4">
          <InputField label="First Name" name="firstName" required={false} />
          <InputField label="Last Name" name="lastName" required={false} />
        </div>
        <Button type="submit" size="sm" disabled={!isDirty}>
          {isSubmitting ? 'Processing...' : 'Update'}
        </Button>
      </form>
    </FormProvider>
  );
}

interface EditProfilePicture extends Profile {
  updateProfile: () => Promise<void>;
}

function EditProfilePicture({ setStatus, updateProfile }: EditProfilePicture) {
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
                  setStatus({ type: 'error', msg: 'Unable to remove profile picture' });
                }
              }}
            >
              <TrashIcon className="h-4 w-4" />
              Remove profile picture
            </button>
          </div>
        </div>
      </div>
      <ProfilePictureUpload
        endpoint={`${import.meta.env.VITE_API_V1_STR}/users/profile`}
        open={open}
        onSuccess={onSuccess}
        setOpen={setOpen}
      />
    </>
  );
}

interface APIAccessForm extends Profile {
  updateProfile: () => Promise<void>;
  user: User;
}

function APIAccessForm({ setStatus, updateProfile, user }: APIAccessForm) {
  const [isSending, setIsSending] = useState(false);

  async function revokeAPIKey() {
    setIsSending(true);
    try {
      const response: AxiosResponse<User> = await axios.get(
        `${import.meta.env.VITE_API_V1_STR}/auth/revoke-api-key`
      );
      if (response) {
        // display API key with COPY API Key button
        if (response) {
          setIsSending(false);
          updateProfile();
        } else {
          setIsSending(false);
          setStatus({ type: 'error', msg: 'Unable to revoke API key' });
        }
      } else {
        setIsSending(false);
        setStatus({ type: 'error', msg: 'Unable to revoke API key' });
      }
    } catch (_err) {
      setIsSending(false);
      setStatus({ type: 'error', msg: 'Unable to revoke API key' });
    }
  }

  async function requestAPIKey() {
    setIsSending(true);
    try {
      const response: AxiosResponse<User> = await axios.get(
        `${import.meta.env.VITE_API_V1_STR}/auth/request-api-key`
      );
      if (response) {
        if (response) {
          setIsSending(false);
          updateProfile();
        } else {
          setIsSending(false);
          setStatus({ type: 'error', msg: 'Unable to get API key' });
        }
      } else {
        setIsSending(false);
        setStatus({ type: 'error', msg: 'Unable to get API key' });
      }
    } catch (_err) {
      setIsSending(false);
      setStatus({ type: 'error', msg: 'Unable to get API key' });
    }
  }

  const exampleURL = `${
    window.location.origin
  }/static/projects/1/flights/1/data_products/1/mygeotiff.tif&API_KEY=${
    user.api_access_token ? user.api_access_token : 'MYKEY'
  }`;

  return (
    <div className="flex flex-col gap-4">
      <span className="text-xl font-semibold">API Key Access</span>

      <div className="flex flex-col gap-4">
        <div>
          <p className="text-sm">
            Your API key is a sensitive credential that can be used to access your data
            stored on {import.meta.env.VITE_BRAND_SHORT}. Please keep it secure and do
            not share it with anyone. If you suspect unauthorized access using your API
            key, you may revoke the key using this form and request a new one.
          </p>
          {user.api_access_token ? (
            <Fragment>
              <span className="text-sm">API Key:</span>
              <div className="flex flex-row items-center justify-between gap-2 px-2 bg-gray-200">
                <span className="font-semibold">{user.api_access_token}</span>
                <DocumentDuplicateIcon
                  className="w-4 h-4 cursor-pointer"
                  onClick={() =>
                    navigator.clipboard.writeText(
                      user.api_access_token ? user.api_access_token : ''
                    )
                  }
                />
              </div>
            </Fragment>
          ) : null}
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="italic text-sm">Example usage:</span>
          <div className="p-4 text-sm bg-gray-200 overflow-x-auto">
            <span>{exampleURL}</span>
          </div>
        </div>
      </div>

      {!user.api_access_token ? (
        <Button type="button" size="sm" onClick={() => requestAPIKey()}>
          {!isSending ? 'Request API Key' : 'Requesting...'}
        </Button>
      ) : (
        <Button type="button" size="sm" onClick={() => revokeAPIKey()}>
          {!isSending ? 'Revoke API Key' : 'Revoking...'}
        </Button>
      )}
    </div>
  );
}

export default function Profile() {
  const { updateProfile, user } = useContext(AuthContext);
  const [showChangePasswordForm, setShowChangePasswordForm] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);

  return (
    <div className="h-full flex flex-row justify-center bg-gradient-to-b from-primary from-20% to-slate-200 to-10%">
      <div className="mt-16 sm:w-full md:w-1/2 max-w-xl">
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
                <EditProfilePicture
                  setStatus={setStatus}
                  updateProfile={updateProfile}
                />
              </div>
              {/* form column */}
              <div className="flex flex-col gap-4">
                <ProfileForm
                  setStatus={setStatus}
                  updateProfile={updateProfile}
                  user={user}
                />
                <APIAccessForm
                  setStatus={setStatus}
                  updateProfile={updateProfile}
                  user={user}
                />
                <span className="text-xl font-semibold">Password Management</span>
                <p>Update your current password by clicking the below button.</p>
                {showChangePasswordForm ? (
                  <ChangePasswordForm
                    setShowChangePasswordForm={setShowChangePasswordForm}
                    setStatus={setStatus}
                  />
                ) : (
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => setShowChangePasswordForm(true)}
                  >
                    Change Password
                  </Button>
                )}
                {status && status.type && status.msg ? (
                  <Alert alertType={status.type}>{status.msg}</Alert>
                ) : null}
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
