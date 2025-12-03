import { AxiosResponse } from 'axios';
import { useState } from 'react';
import { useLoaderData } from 'react-router-dom';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';

import Alert, { Status } from '../../../Alert';
import { User } from '../../../../AuthContext';
import { Team } from '../../teams/Teams';
import TeamExtensions from './TeamExtensions';
import UserExtensions from './UserExtensions';

import api from '../../../../api';
import { sorter } from '../../../utils';

type Extension = {
  id: string;
  description: string;
  name: string;
};

export async function loader() {
  try {
    const extensions: AxiosResponse<Extension[]> = await api.get(
      '/admin/extensions'
    );
    const teams: AxiosResponse<Team[]> = await api.get('teams');
    const users: AxiosResponse<User[]> = await api.get('/admin/users');
    if (extensions && teams && users) {
      return {
        extensions: extensions.data,
        teams: teams.data.sort((a, b) => sorter(a.title, b.title)),
        users: users.data.sort((a, b) => sorter(a.first_name, b.first_name)),
      };
    } else {
      return { extensions: [], teams: [], users: [] };
    }
  } catch (err) {
    console.error(err);
    return { extensions: [], teams: [], users: [] };
  }
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

  return (
    <section className="w-full bg-white">
      <div className="flex flex-col gap-8 h-full px-4 py-12 sm:px-6 md:py-16 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            Manage Extensions
          </h2>

          <p className="mt-4 text-gray-500 sm:text-xl">
            Activate extensions for individuals and teams.
          </p>
        </div>

        {extensions.length > 0 && (
          <TabGroup selectedIndex={selectedIndex} onChange={setSelectedIndex}>
            <TabList>
              <Tab className="data-selected:bg-accent3 data-selected:text-white data-hover:underline w-28 shrink-0 rounded-lg p-2 font-medium">
                Teams
              </Tab>
              <Tab className="data-selected:bg-accent3 data-selected:text-white data-hover:underline w-28 shrink-0 rounded-lg p-2 font-medium">
                Users
              </Tab>
            </TabList>
            <hr className="my-4 border-gray-300" />
            <TabPanels>
              <TabPanel>
                <TeamExtensions
                  extensions={extensions}
                  setStatus={setStatus}
                  teams={teams}
                />
              </TabPanel>
              <TabPanel>
                <UserExtensions
                  extensions={extensions}
                  setStatus={setStatus}
                  users={users}
                />
              </TabPanel>
            </TabPanels>
          </TabGroup>
        )}
        {extensions.length < 1 && (
          <div className="my-24 flex items-center justify-center">
            <span className="text-lg font-semibold">
              No extensions to manage
            </span>
          </div>
        )}
        {status && <Alert alertType={status.type}>{status.msg}</Alert>}
      </div>
    </section>
  );
}
