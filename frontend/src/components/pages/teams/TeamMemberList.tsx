import { isAxiosError } from 'axios';
import clsx from 'clsx';
import { useContext, useMemo, useState } from 'react';
import { useLoaderData, useParams, useRevalidator } from 'react-router-dom';

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
    return <div>No team members</div>;
  } else {
    return (
      <div className="h-full overflow-y-auto">
        <div className="h-3/4">
          <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
            <thead className="sticky top-0 z-10 bg-white border-b-2 border-gray-200">
              <tr>
                <th
                  className={clsx(
                    'whitespace-nowrap px-4 py-2 font-medium text-gray-900 text-left',
                    hasWriteAccess && 'w-[30%]',
                    !hasWriteAccess && 'w-[40%]'
                  )}
                >
                  Name
                </th>
                <th
                  className={clsx(
                    'whitespace-nowrap px-4 py-2 font-medium text-gray-900 text-left',
                    hasWriteAccess && 'w-[30%]',
                    !hasWriteAccess && 'w-[40%]'
                  )}
                >
                  Email
                </th>
                <th
                  className={
                    'whitespace-nowrap px-4 py-2 font-medium text-gray-900 text-center w-[20%]'
                  }
                >
                  Role
                </th>
                {hasWriteAccess && (
                  <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900 text-center w-[20%]">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
          </table>
          <div className="h-full overflow-y-auto">
            <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
              <tbody className="divide-y divide-gray-200">
                {sortedTeamMembers.map((teamMember) => (
                  <tr key={teamMember.id} className="odd:bg-gray-50">
                    <td
                      className={clsx(
                        'gap-4 whitespace-nowrap px-4 py-2 font-medium text-gray-900 text-left',
                        hasWriteAccess && 'w-[30%]',
                        !hasWriteAccess && 'w-[40%]'
                      )}
                    >
                      <div className="flex items-center justify-start gap-4">
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
                        <span>{teamMember.full_name}</span>
                      </div>
                    </td>
                    <td
                      className={clsx(
                        'whitespace-nowrap px-4 py-2 text-gray-700 text-left',
                        hasWriteAccess && 'w-[30%]',
                        !hasWriteAccess && 'w-[40%]'
                      )}
                    >
                      {teamMember.email}
                    </td>
                    <td className="whitespace-nowrap px-4 py-2 text-gray-700 text-center w-[20%]">
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
                      <td className="px-4 py-2 text-center w-[20%]">
                        {user && teamMember.email !== user.email && (
                          <button
                            className="text-sky-600"
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
      </div>
    );
  }
}
