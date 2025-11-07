import { AxiosResponse } from 'axios';
import { useContext, useEffect, useMemo, useState } from 'react';
import {
  Params,
  useLoaderData,
  useNavigate,
  useRevalidator,
} from 'react-router-dom';

import AuthContext from '../../../AuthContext';
import { Button } from '../../Buttons';
import { ConfirmationPopup } from '../../ConfirmationPopup';
import Modal from '../../Modal';
import TeamEditForm from './TeamEditForm';
import TeamMemberList from './TeamMemberList';

import SearchUsers, { UserSearch } from './SearchUsers';

import api from '../../../api';

export type Role = 'owner' | 'manager' | 'viewer';

interface Team {
  id: string;
  is_owner: boolean;
  title: string;
  description: string;
}

export interface TeamMember {
  id: string;
  email: string;
  full_name: string;
  member_id: string;
  profile_url: string | null;
  role: Role;
  team_id: string;
}

export interface TeamData {
  team: Team;
  members: TeamMember[];
}

// fetches team details and team members prior to render
export async function loader({ params }: { params: Params<string> }) {
  try {
    const teamResponse: AxiosResponse<Team> = await api.get(
      `/teams/${params.teamId}`
    );
    const teamMembers: AxiosResponse<TeamMember[]> = await api.get(
      `/teams/${params.teamId}/members`
    );
    if (teamResponse && teamMembers) {
      return { team: teamResponse.data, members: teamMembers.data };
    } else {
      return { team: null, members: [] };
    }
  } catch (err) {
    throw err;
  }
}

export default function TeamDetail() {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const revalidator = useRevalidator();
  const [open, setOpen] = useState(false);
  const teamData = useLoaderData() as TeamData;
  const [searchResults, setSearchResults] = useState<UserSearch[]>([]);

  // Save last viewed team to localStorage
  useEffect(() => {
    if (teamData?.team?.id) {
      localStorage.setItem('lastViewedTeamId', teamData.team.id);
    }
  }, [teamData?.team?.id]);

  const hasWriteAccess = useMemo(
    () =>
      teamData.members
        .find((member) => member.member_id === user?.id)
        ?.role.toLowerCase() === 'owner' ||
      teamData.members
        .find((member) => member.member_id === user?.id)
        ?.role.toLowerCase() === 'manager',
    [teamData.members, user]
  );

  const hasDeleteAccess = useMemo(
    () =>
      teamData.members
        .find((member) => member.member_id === user?.id)
        ?.role.toLowerCase() === 'owner',
    [teamData.members, user]
  );

  return (
    <div className="flex flex-col h-full">
      {/* Fixed header - team info */}
      <div className="flex-none px-2 sm:px-0">
        {hasWriteAccess ? (
          <TeamEditForm teamData={teamData} />
        ) : (
          <div className="grid rows-auto gap-2">
            <h2 className="mb-0 text-xl sm:text-2xl">{teamData.team.title}</h2>
            <span className="text-gray-600 text-sm sm:text-base">
              {teamData.team.description}
            </span>
          </div>
        )}
        <hr className="border-gray-700 my-4" />
      </div>

      {/* Scrollable content area */}
      <div className="flex-1 min-h-0 overflow-y-auto px-2 sm:px-0 sm:pr-2">
        <div className="space-y-6 pb-6">
          {/* Members section */}
          <div>
            <h2 className="mb-4 text-lg sm:text-xl">
              {teamData.team.title} Members
            </h2>
            <TeamMemberList
              teamMembers={teamData.members}
              hasDeleteAccess={hasDeleteAccess}
              hasWriteAccess={hasWriteAccess}
            />
          </div>

          {/* Add members section - only if has write access */}
          {hasWriteAccess && (
            <div className="border-t border-gray-300 pt-6">
              <h3 className="mb-4 text-base sm:text-lg">
                Find new team members
              </h3>
              <div className="space-y-4">
                <SearchUsers
                  currentMembers={teamData.members}
                  searchResults={searchResults}
                  setSearchResults={setSearchResults}
                  user={user}
                />
                {searchResults.length > 0 &&
                searchResults.filter((u) => u.checked).length > 0 && (
                  <Button
                    size="sm"
                    onClick={(e) => {
                      e.preventDefault();
                      let selectedMembers = searchResults
                        .filter((u) => u.checked)
                        .filter(
                          (newMember) =>
                            teamData.members
                              .map((currentMember) => currentMember.email)
                              .indexOf(newMember.email) < 0
                        );

                      if (selectedMembers.length > 0) {
                        api
                          .post(
                            `/teams/${teamData.team.id}/members/multi`,
                            selectedMembers.map(({ id }) => id)
                          )
                          .then(() => {
                            setSearchResults([]);
                            revalidator.revalidate();
                          })
                          .catch((err) => console.error(err));
                      }
                    }}
                  >
                    Add Selected
                  </Button>
                )}
              </div>

              {/* Delete team section */}
              <div className="mt-6 pt-6 border-t border-gray-300">
                <div className="w-full sm:w-48">
                  <Button
                    type="button"
                    size="sm"
                    icon="trash"
                    onClick={() => setOpen(true)}
                  >
                    Delete team
                  </Button>
                </div>
                <Modal open={open} setOpen={setOpen}>
                  <ConfirmationPopup
                    title="Are you sure you want to delete this team?"
                    content="Deleting this team will cause all team members to immediately lose access to any projects, flights, and data associated with the team."
                    confirmText="Yes, remove team"
                    rejectText="No, keep team"
                    setOpen={setOpen}
                    onConfirm={async () => {
                      try {
                        const response = await api.delete(
                          `/teams/${teamData.team.id}`
                        );
                        if (response) {
                          setOpen(false);
                          navigate('/teams', { state: { reload: true } });
                        } else {
                          setOpen(false);
                        }
                      } catch (err) {
                        setOpen(false);
                      }
                    }}
                  />
                </Modal>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
