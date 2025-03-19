import { isAxiosError, AxiosResponse } from 'axios';
import { useRevalidator } from 'react-router-dom';

import { confirm } from '../../ConfirmationDialog';
import { Role, TeamMember } from './TeamDetail';

import api from '../../../api';

export default function TeamMemberRoleRadioGroup({
  disabled = false,
  isCurrentUser = false,
  teamId,
  teamMember,
  userRole = 'viewer',
}: {
  disabled?: boolean;
  isCurrentUser?: boolean;
  teamId: string;
  teamMember: TeamMember;
  userRole?: Role;
}) {
  const revalidator = useRevalidator();

  const updateTeamMemberRole = async (newRole: string) => {
    try {
      const response: AxiosResponse<TeamMember> = await api.put(
        `/teams/${teamId}/members/${teamMember.id}`,
        {
          role: newRole,
        }
      );
      if (response.status === 200) {
        revalidator.revalidate();
      } else {
        console.error('An unexpected error occurred.');
      }
    } catch (error) {
      if (isAxiosError(error)) {
        const status = error.response?.status || 500;
        const message = error.response?.data?.message || error.message;
        console.error(
          `Failed to update team member role: ${status} -- ${message}`
        );
      } else {
        console.error('An unexpected error occurred.');
      }
    }
  };

  const handleOnChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const newRole = e.target.value;
    if (isCurrentUser && newRole === 'viewer') {
      if (
        await confirm({
          title: 'Change Role',
          description:
            'You are about to change your role to Viewer. You will not be able to reverse this action.',
          confirmation: 'Are you sure you want to change your role to Viewer?',
        })
      ) {
        updateTeamMemberRole(newRole);
      }
    } else {
      if (
        await confirm({
          title: 'Change Role',
          description:
            "You are about to change a team member's role. This will affect their access to the team and any associated projects. Their role in those projects will be updated to match their new team member role.",
          confirmation: `Are you sure you want to change ${teamMember.full_name}'s role to ${newRole}?`,
        })
      ) {
        updateTeamMemberRole(newRole);
      }
    }
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
        disabled={userRole !== 'owner'}
        title={
          userRole !== 'owner'
            ? 'You are not authorized to change the role of this team member'
            : ''
        }
      />
      <label htmlFor={`owner-${teamMember.id}`}>Owner</label>
      <input
        className="form-radio h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        type="radio"
        id={`manager-${teamMember.id}`}
        name={`role-${teamMember.id}`}
        value="manager"
        checked={teamMember.role === 'manager'}
        onChange={handleOnChange}
        disabled={disabled}
        title={disabled ? 'Team creator cannot be demoted' : ''}
      />
      <label htmlFor={`manager-${teamMember.id}`}>Manager</label>
      <input
        className="form-radio h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        type="radio"
        id={`viewer-${teamMember.id}`}
        name={`role-${teamMember.id}`}
        value="viewer"
        checked={teamMember.role === 'viewer'}
        onChange={handleOnChange}
        disabled={disabled}
        title={disabled ? 'Team creator cannot be demoted' : ''}
      />
      <label htmlFor={`viewer-${teamMember.id}`}>Viewer</label>
    </div>
  );
}
