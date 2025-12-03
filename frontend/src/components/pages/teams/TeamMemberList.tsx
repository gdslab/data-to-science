import { isAxiosError } from 'axios';
import clsx from 'clsx';
import { useContext, useMemo, useState } from 'react';
import { useLoaderData, useParams, useRevalidator } from 'react-router';

import Alert, { Status } from '../../Alert';
import AuthContext from '../../../AuthContext';
import { generateRandomProfileColor } from '../auth/Profile';
import { TeamData, TeamMember } from './TeamDetail';
import TeamMemberRoleRadioGroup from './TeamMemberRoleRadioGroup';

import api from '../../../api';
import { sorter } from '../../utils';

export default function TeamMemberList({
  hasWriteAccess = false,
  hasDeleteAccess = false,
  teamMembers,
}: {
  hasDeleteAccess?: boolean;
  hasWriteAccess?: boolean;
  teamMembers: TeamMember[];
}) {
  const [status, setStatus] = useState<Status | null>(null);
  const { team } = useLoaderData() as TeamData;
  const { teamId } = useParams();
  const revalidator = useRevalidator();
  const { user } = useContext(AuthContext);

  async function removeTeamMember(memberId: string) {
    setStatus(null);
    try {
      await api.delete(`/teams/${teamId}/members/${memberId}`);
      revalidator.revalidate();
    } catch (error) {
      if (isAxiosError(error)) {
        const statusCode = error.response?.status || 500;
        const message = error.response?.data?.message || error.message;
        console.error(
          `Failed to remove team member: ${statusCode} -- ${message}`
        );
        setStatus({
          type: 'error',
          msg: message,
        });
      } else {
        console.error('An unexpected error occurred.');
        setStatus({
          type: 'error',
          msg: 'An unexpected error occurred.',
        });
      }
    }
  }

  const sortedTeamMembers = useMemo(
    () => teamMembers.sort((a, b) => sorter(a.full_name, b.full_name)),
    [teamMembers]
  );

  const userRole = useMemo(() => {
    return teamMembers.find((member) => member.member_id === user?.id)?.role;
  }, [teamMembers, user]);

  if (teamMembers.length < 1) {
    return <div className="text-sm sm:text-base text-gray-600">No team members</div>;
  } else {
    return (
      <div>
        <div className="max-h-96 overflow-y-auto overflow-x-auto border border-gray-200 rounded-lg shadow-xs">
          <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-xs sm:text-sm">
            <thead className="sticky top-0 z-10 bg-white border-b-2 border-gray-200">
              <tr>
                <th
                  className={clsx(
                    'whitespace-nowrap px-2 sm:px-4 py-2 font-medium text-gray-900 text-left',
                    hasWriteAccess ? 'min-w-[150px] sm:w-[30%]' : 'min-w-[180px] sm:w-[40%]'
                  )}
                >
                  Name
                </th>
                <th
                  className={clsx(
                    'whitespace-nowrap px-2 sm:px-4 py-2 font-medium text-gray-900 text-left',
                    hasWriteAccess ? 'min-w-[150px] sm:w-[30%]' : 'min-w-[180px] sm:w-[40%]'
                  )}
                >
                  Email
                </th>
                <th className="whitespace-nowrap px-2 sm:px-4 py-2 font-medium text-gray-900 text-center min-w-[100px] sm:w-[20%]">
                  Role
                </th>
                {hasWriteAccess && (
                  <th className="whitespace-nowrap px-2 sm:px-4 py-2 font-medium text-gray-900 text-center min-w-[80px] sm:w-[20%]">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sortedTeamMembers.map((teamMember) => (
                <tr key={teamMember.id} className="odd:bg-gray-50">
                  <td
                    className={clsx(
                      'gap-2 sm:gap-4 whitespace-nowrap px-2 sm:px-4 py-2 font-medium text-gray-900 text-left',
                      hasWriteAccess ? 'min-w-[150px] sm:w-[30%]' : 'min-w-[180px] sm:w-[40%]'
                    )}
                  >
                    <div className="flex items-center justify-start gap-2 sm:gap-4">
                      {teamMember.profile_url ? (
                        <img
                          key={teamMember.profile_url
                            .split('/')
                            .slice(-1)[0]
                            .slice(0, -4)}
                          className="h-6 w-6 sm:h-8 sm:w-8 rounded-full shrink-0"
                          src={teamMember.profile_url}
                        />
                      ) : (
                        <div
                          className="flex items-center justify-center h-6 w-6 sm:h-8 sm:w-8 text-white text-xs sm:text-sm rounded-full shrink-0"
                          style={generateRandomProfileColor(
                            teamMember.full_name
                          )}
                        >
                          <span className="indent-[0.1em] tracking-widest">
                            {teamMember.full_name[0] +
                              teamMember.full_name.split(' ').slice(-1)[0][0]}
                          </span>
                        </div>
                      )}
                      <span className="truncate">{teamMember.full_name}</span>
                    </div>
                  </td>
                  <td
                    className={clsx(
                      'whitespace-nowrap px-2 sm:px-4 py-2 text-gray-700 text-left',
                      hasWriteAccess ? 'min-w-[150px] sm:w-[30%]' : 'min-w-[180px] sm:w-[40%]'
                    )}
                  >
                    <span className="truncate block">{teamMember.email}</span>
                  </td>
                  <td className="whitespace-nowrap px-2 sm:px-4 py-2 text-gray-700 text-center min-w-[100px] sm:w-[20%]">
                    {hasWriteAccess ? (
                      <TeamMemberRoleRadioGroup
                        teamId={team.id}
                        teamMember={teamMember}
                        disabled={
                          team.is_owner && teamMember.member_id === user?.id
                        }
                        isCurrentUser={teamMember.member_id === user?.id}
                        setStatus={setStatus}
                        userRole={userRole}
                      />
                    ) : (
                      teamMember.role.slice(0, 1).toUpperCase() +
                      teamMember.role.slice(1)
                    )}
                  </td>
                  {hasDeleteAccess && hasWriteAccess && (
                    <td className="px-2 sm:px-4 py-2 text-center min-w-[80px] sm:w-[20%]">
                      {user && teamMember.email !== user.email && (
                        <button
                          className="text-sky-600 hover:text-sky-800 text-xs sm:text-sm py-1 px-2 touch-manipulation"
                          type="button"
                          onClick={() => removeTeamMember(teamMember.id)}
                        >
                          Remove
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {status && (
          <div className="mt-4">
            <Alert alertType={status.type}>{status.msg}</Alert>
          </div>
        )}
      </div>
    );
  }
}
