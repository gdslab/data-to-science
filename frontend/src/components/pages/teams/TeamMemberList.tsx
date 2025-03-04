import { useContext, useMemo } from 'react';
import { useLoaderData, useParams, useRevalidator } from 'react-router-dom';

import AuthContext from '../../../AuthContext';
import { generateRandomProfileColor } from '../auth/Profile';
import { TeamData, TeamMember } from './TeamDetail';

import api from '../../../api';
import { sorter } from '../../utils';

function TeamMemberRole({
  disabled = true,
  teamMember,
}: {
  disabled?: boolean;
  teamMember: TeamMember;
}) {
  const handleOnChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Send API request to update team member role
  };

  return (
    <div className="flex gap-4">
      <input
        className="form-radio h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        type="radio"
        id={`owner-${teamMember.id}`}
        name={`role-${teamMember.id}`}
        value="owner"
        checked={teamMember.role === 'owner'}
        onChange={handleOnChange}
        disabled={disabled}
      />
      <label htmlFor={`owner-${teamMember.id}`}>Owner</label>
      <input
        className="form-radio h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        type="radio"
        id={`member-${teamMember.id}`}
        name={`role-${teamMember.id}`}
        value="member"
        checked={teamMember.role === 'member'}
        onChange={handleOnChange}
        disabled={disabled}
      />
      <label htmlFor={`member-${teamMember.id}`}>Member</label>
    </div>
  );
}

export default function TeamMemberList({
  teamMembers,
}: {
  teamMembers: TeamMember[];
}) {
  const { team } = useLoaderData() as TeamData;
  const { teamId } = useParams();
  const revalidator = useRevalidator();
  const { user } = useContext(AuthContext);

  async function removeTeamMember(memberId: string) {
    try {
      const response = await api.delete(`/teams/${teamId}/members/${memberId}`);
      if (response) {
        revalidator.revalidate();
      }
    } catch (err) {
      console.error(err);
    }
  }

  const sortedTeamMembers = useMemo(
    () => teamMembers.sort((a, b) => sorter(a.full_name, b.full_name)),
    [teamMembers]
  );

  if (teamMembers.length < 1) {
    return <div>No team members</div>;
  } else {
    return (
      <div className="h-full overflow-y-auto">
        <div className="h-1/2">
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
              {sortedTeamMembers.map((teamMember) => (
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
                    {team.is_owner ? (
                      <TeamMemberRole
                        disabled={!team.is_owner}
                        teamMember={teamMember}
                      />
                    ) : (
                      teamMember.role.slice(0, 1).toUpperCase() +
                      teamMember.role.slice(1)
                    )}
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
