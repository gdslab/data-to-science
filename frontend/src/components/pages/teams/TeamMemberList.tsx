import axios from 'axios';
import { useContext } from 'react';
import { useLoaderData, useParams, useRevalidator } from 'react-router-dom';
import { UserMinusIcon } from '@heroicons/react/24/outline';

import AuthContext from '../../../AuthContext';
import { TeamData, TeamMember } from './TeamDetail';
import { sorter } from '../../utils';

export default function TeamMemberList({ teamMembers }: { teamMembers: TeamMember[] }) {
  const { team } = useLoaderData() as TeamData;
  const { teamId } = useParams();
  const revalidator = useRevalidator();
  const { user } = useContext(AuthContext);

  async function removeTeamMember(memberId: string) {
    try {
      const response = await axios.delete(
        `/api/v1/teams/${teamId}/members/${memberId}`
      );
      if (response) {
        revalidator.revalidate();
      }
    } catch (err) {
      console.error(err);
    }
  }

  if (teamMembers.length < 1) {
    return <div>No team members</div>;
  } else {
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
          <thead className="text-left">
            <tr>
              <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                Name
              </th>
              <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                Email
              </th>
              <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                Role
              </th>
              {team.is_owner ? (
                <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                  Actions
                </th>
              ) : null}
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-200">
            {teamMembers
              .sort((a, b) => sorter(a.full_name, b.full_name))
              .map((teamMember) => (
                <tr key={teamMember.id} className="odd:bg-gray-50">
                  <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                    {teamMember.full_name}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                    {teamMember.email}
                  </td>
                  <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                    {team.is_owner && user && teamMember.email === user.email
                      ? 'Owner'
                      : 'Member'}
                  </td>
                  {team.is_owner ? (
                    <td className="text-center">
                      {user && teamMember.email !== user.email ? (
                        <button
                          type="button"
                          onClick={() => removeTeamMember(teamMember.id)}
                        >
                          <UserMinusIcon className="h-6 w-6" aria-hidden="true" />
                        </button>
                      ) : null}
                    </td>
                  ) : null}
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    );
  }
}
