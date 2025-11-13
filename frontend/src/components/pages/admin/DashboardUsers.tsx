import { AxiosResponse } from 'axios';
import { useMemo, useState } from 'react';
import { useLoaderData } from 'react-router-dom';

import DashboardUserList from './DashboardUserList';
import SearchBar from './SearchBar';
import StatCard from './StatCard';
import StatCardWithPeriodToggle from './StatCardWithPeriodToggle';
import { User } from '../../../AuthContext';

import api from '../../../api';
import { sorter } from '../../utils';

export async function loader() {
  const response: AxiosResponse<User[]> = await api.get('/admin/users');
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

/**
 * Return number of active users that joined in last N days.
 * @param users List of users on platform.
 * @param nDays Number of days.
 * @returns Active users registered within number of days.
 */
function joinedInLastNDays(users: User[], nDays: number): number {
  const pastDate = new Date();
  // update today to today's date - number of days
  pastDate.setDate(pastDate.getDate() - nDays);
  const filteredUsers = users.filter(
    (user) =>
      new Date(user.created_at).getTime() > pastDate.getTime() &&
      user.is_approved &&
      user.is_email_confirmed
  );
  return filteredUsers.length;
}

/**
 * Return number of active users (approved and email confirmed).
 * @param users List of users on platform.
 * @returns Count of active users.
 */
function countActiveUsers(users: User[]): number {
  return users.filter(
    (user) => user.is_approved && user.is_email_confirmed
  ).length;
}

/**
 * Return number of users awaiting email confirmation.
 * @param users List of users on platform.
 * @returns Count of users with unconfirmed email.
 */
function countAwaitingEmailConfirmation(users: User[]): number {
  return users.filter((user) => !user.is_email_confirmed).length;
}

/**
 * Return number of users awaiting admin approval.
 * @param users List of users on platform.
 * @returns Count of users awaiting approval.
 */
function countAwaitingApproval(users: User[]): number {
  return users.filter((user) => !user.is_approved).length;
}

export default function DashboardUsers() {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const loadedUsers = useLoaderData() as User[];
  const [users, setUsers] = useState<User[]>(loadedUsers);

  // Sync users when loadedUsers changes
  useMemo(() => {
    setUsers(loadedUsers);
  }, [loadedUsers]);

  const updateSearchTerm = (newSearchTerm: string): void =>
    setSearchTerm(newSearchTerm);

  const filteredUsers = useMemo(() => {
    // If searchTerm is empty, return all users
    if (searchTerm === '') {
      return users
        .slice()
        .sort((a, b) =>
          sorter(a.last_name.toLowerCase(), b.last_name.toLowerCase())
        );
    }

    const lowerSearchTerm = searchTerm.toLowerCase();

    return users
      .filter(
        (user) =>
          user.first_name.toLowerCase().includes(lowerSearchTerm) ||
          user.last_name.toLowerCase().includes(lowerSearchTerm) ||
          user.email.toLowerCase().includes(searchTerm)
      )
      .sort((a, b) =>
        sorter(a.last_name.toLowerCase(), b.last_name.toLowerCase())
      );
  }, [searchTerm, users]);

  return (
    <section className="w-full bg-white">
      <div className="flex flex-col gap-8 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            Users
          </h2>

          <p className="mt-4 text-gray-500 sm:text-xl">
            List of registered users on this D2S instance.
          </p>
        </div>

        <div>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard title="Total Active Users" value={countActiveUsers(users)} />
            <StatCard
              title="Awaiting Email Confirmation"
              value={countAwaitingEmailConfirmation(users)}
            />
            <StatCard
              title="Awaiting Admin Approval"
              value={countAwaitingApproval(users)}
            />
            <StatCardWithPeriodToggle
              getValue={(period) => joinedInLastNDays(users, period)}
            />
          </dl>
        </div>

        <SearchBar
          searchTerm={searchTerm}
          updateSearchTerm={updateSearchTerm}
        />

        <DashboardUserList users={filteredUsers} setUsers={setUsers} />
      </div>
    </section>
  );
}
