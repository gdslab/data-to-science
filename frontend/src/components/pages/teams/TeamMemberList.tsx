import axios from 'axios';
import { useContext } from 'react';
import { useLoaderData, useParams, useRevalidator } from 'react-router-dom';

import AuthContext from '../../../AuthContext';
import { generateRandomProfileColor } from '../auth/Profile';
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
      <div className="overflow-y-auto">
        <div className="max-h-[25vh]">
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
                    <td className="flex items-center justify-start gap-4 whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                      {teamMember.profile_url ? (
                        <img
                          key={teamMember.profile_url
                            .split('/')
                            .slice(-1)[0]
                            .slice(0, -4)}
                          className="h-8 w-8 rounded-full"
                          src={teamMember.profile_url}
                        />
                      ) : (
                        <div
                          className="flex items-center justify-center h-8 w-8 text-white text-sm rounded-full"
                          style={generateRandomProfileColor(teamMember.full_name)}
                        >
                          <span className="indent-[0.1em] tracking-widest">
                            {teamMember.full_name[0] +
                              teamMember.full_name.split(' ').slice(-1)[0][0]}
                          </span>
                        </div>
                      )}
                      <span>{teamMember.full_name}</span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                      {teamMember.email}
                    </td>
                    <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                      {teamMember.role === 'owner' ? 'Owner' : 'Member'}
                    </td>
                    {team.is_owner ? (
                      <td className="px-4 py-2">
                        {user && teamMember.email !== user.email ? (
                          <button
                            className="text-sky-600"
                            type="button"
                            onClick={() => removeTeamMember(teamMember.id)}
                          >
                            Remove
                          </button>
                        ) : null}
                      </td>
                    ) : null}
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
}
