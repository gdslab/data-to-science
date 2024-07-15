import axios, { AxiosResponse } from 'axios';
import { useState } from 'react';
import { useLoaderData, useRevalidator } from 'react-router-dom';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';

import { Team } from '../teams/Teams';
import Alert, { Status } from '../../Alert';
import { User } from '../../../AuthContext';

type Extension = {
  id: string;
  description: string;
  name: string;
};

export async function loader() {
  try {
    const extensions: AxiosResponse<Extension[]> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/admin/extensions`
    );
    const teams: AxiosResponse<Team[]> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/teams`
    );
    const users: AxiosResponse<User[]> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/users`
    );
    if (extensions && teams && users) {
      return {
        extensions: extensions.data,
        teams: teams.data.map((team) => ({ ...team, extensions: [] })),
        users: users.data.map((user) => ({ ...user, extensions: [] })),
      };
    } else {
      return { extensions: [], teams: [], users: [] };
    }
  } catch (err) {
    console.error(err);
    return { extensions: [], teams: [], users: [] };
  }
}

type ExtensionList = {
  extensions: Extension[];
  selectedExtensions: string[];
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
  teamId?: string;
  userId?: string;
};

function ExtensionList({
  extensions,
  selectedExtensions,
  setStatus,
  teamId,
  userId,
}: ExtensionList) {
  const revalidator = useRevalidator();

  if (!teamId && !userId) {
    console.error('Must provide team or user id');
    return;
  }

  async function handleOnChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (teamId) {
      // send api request to toggle on extension for team
      try {
        const payload = {
          teamId: teamId,
          extensionId: e.target.value,
          activate: e.target.checked,
        };
        const response = await axios.put(
          `${import.meta.env.VITE_API_V1_STR}/admin/extensions/team`,
          payload
        );
        if (response.status === 200) {
          // update status
          setStatus({
            type: 'success',
            msg: `Extension ${e.target.checked ? 'activated' : 'deactivated'}`,
          });
          revalidator.revalidate();
        } else {
          // update status
          setStatus({ type: 'error', msg: 'Unable to change extension' });
        }
      } catch (err) {
        console.error(err);
        setStatus({ type: 'error', msg: 'Unable to change extension' });
      }
    }
    if (userId) {
      // send api request to toggle on extension for user
      try {
        const payload = {
          userId: userId,
          extensionId: e.target.value,
          activate: e.target.checked,
        };
        const response = await axios.put(
          `${import.meta.env.VITE_API_V1_STR}/admin/extensions/user`,
          payload
        );
        if (response.status === 200) {
          // update status
          setStatus({
            type: 'success',
            msg: `Extension ${e.target.checked ? 'activated' : 'deactivated'}`,
          });
          revalidator.revalidate();
        } else {
          // update status
          setStatus({ type: 'error', msg: 'Unable to change extension' });
        }
      } catch (err) {
        console.error(err);
        setStatus({ type: 'error', msg: 'Unable to change extension' });
      }
    }
  }

  return (
    <div className="flex gap-4">
      {extensions.map((extension) => (
        <div className="flex items-center">
          <input
            type="checkbox"
            id={extension.id}
            name={extension.name}
            value={extension.id}
            className="w-4 h-4 text-accent2 accent-slate-600 bg-gray-100 border-gray-300 rounded focus:ring-accent2/70 focus:ring-2"
            onChange={handleOnChange}
            checked={selectedExtensions.includes(extension.name)}
          />
          <label
            htmlFor={extension.id}
            className="ms-2 text-sm font-medium text-gray-900"
            title={extension.description}
          >
            {extension.name}
          </label>
        </div>
      ))}
    </div>
  );
}

type LoaderData = {
  extensions: Extension[];
  teams: Team[];
  users: User[];
};

export default function DashboardExtensions() {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [status, setStatus] = useState<Status | null>(null);

  const { extensions, teams, users } = useLoaderData() as LoaderData;

  console.log(extensions);

  return (
    <section className="w-full bg-white">
      <div className="mx-auto max-w-screen-xl px-4 py-12 sm:px-6 md:py-16 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            Manage Extensions
          </h2>

          <p className="mt-4 text-gray-500 sm:text-xl">
            Activate extensions for individuals and teams.
          </p>
        </div>

        <TabGroup selectedIndex={selectedIndex} onChange={setSelectedIndex}>
          <TabList>
            <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
              Teams
            </Tab>
            <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
              Users
            </Tab>
          </TabList>
          <hr className="my-4 border-gray-300" />
          <TabPanels>
            <TabPanel>
              <div className="mt-8 sm:mt-12">
                <h3>Teams</h3>
                <table className="relative border-separate border-spacing-y-1 border-spacing-x-1">
                  <thead>
                    <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
                      <th>Name</th>
                      <th>Extensions</th>
                    </tr>
                  </thead>
                  <tbody className="max-h-96 overflow-y-auto">
                    {teams.map((team) => (
                      <tr key={team.id} className="text-center">
                        <td className="p-4 bg-slate-100">{team.title}</td>
                        <td className="p-4 bg-white">
                          <ExtensionList
                            extensions={extensions}
                            selectedExtensions={team.extensions}
                            setStatus={setStatus}
                            teamId={team.id}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </TabPanel>
            <TabPanel>
              <div className="mt-8 sm:mt-12">
                <h3>Users</h3>
                <table className="relative border-separate border-spacing-y-1 border-spacing-x-1">
                  <thead>
                    <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
                      <th>Name</th>
                      <th>Email</th>
                      <th>Extensions</th>
                    </tr>
                  </thead>
                  <tbody className="max-h-96 overflow-y-auto">
                    {users.map((user) => (
                      <tr key={user.id} className="text-center">
                        <td className="p-4 bg-white">
                          {user.first_name} {user.last_name}
                        </td>
                        <td className="p-4 bg-white">{user.email}</td>
                        <td className="p-4 bg-white">
                          <ExtensionList
                            extensions={extensions}
                            selectedExtensions={user.extensions}
                            setStatus={setStatus}
                            userId={user.id}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </TabPanel>
          </TabPanels>
        </TabGroup>
      </div>

      {status && <Alert alertType={status.type}>{status.msg}</Alert>}
    </section>
  );
}
