import { isAxiosError, AxiosResponse } from 'axios';
import { useRevalidator } from 'react-router-dom';

import { confirm } from '../../ConfirmationDialog';
import { TeamMember } from './TeamDetail';

import api from '../../../api';

export default function TeamMemberRoleRadioGroup({
  disabled = false,
  isCurrentUser = false,
  teamId,
  teamMember,
}: {
  disabled?: boolean;
  isCurrentUser?: boolean;
  teamId: string;
  teamMember: TeamMember;
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
        // Optionally, display an error message instead of rethrowing
      } else {
        console.error('An unexpected error occurred.');
      }
    }
  };

  const handleOnChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const newRole = e.target.value;
    if (isCurrentUser && newRole === 'member') {
      if (
        await confirm({
          title: 'Change Role',
          description:
            'You are about to change your role to Member. You will not be able to reverse this action.',
          confirmation:
            'Are you sure you want to change your role from Owner to Member?',
        })
      ) {
        updateTeamMemberRole(newRole);
      }
    } else {
      updateTeamMemberRole(newRole);
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
        title={disabled ? 'Team creator cannot be demoted' : ''}
      />
      <label htmlFor={`member-${teamMember.id}`}>Member</label>
    </div>
  );
}
