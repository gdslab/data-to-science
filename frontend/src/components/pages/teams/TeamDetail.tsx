import { useContext, useState } from 'react';
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

interface Team {
  id: string;
  is_owner: boolean;
  title: string;
  description: string;
}

export interface TeamMember {
  id: string;
  full_name: string;
  email: string;
  profile_url: string | null;
  role: string;
}

export interface TeamData {
  team: Team;
  members: TeamMember[];
}

// fetches team details and team members prior to render
export async function loader({ params }: { params: Params<string> }) {
  try {
    const teamResponse = await api.get(`/teams/${params.teamId}`);
    const teamMembers = await api.get(`/teams/${params.teamId}/members`);
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

  return (
    <div className="flex flex-col gap-4 h-full overflow-hidden">
      <div className="flex-none flex flex-col gap-4">
        {teamData.team.is_owner ? (
          <TeamEditForm teamData={teamData} />
        ) : (
          <div className="grid rows-auto gap-2">
            <h2 className="mb-0">{teamData.team.title}</h2>
            <span className="text-gray-600">{teamData.team.description}</span>
          </div>
        )}
        <hr className="border-gray-700" />
      </div>
      <div className="flex-grow overflow-hidden">
        <h2>{teamData.team.title} Members</h2>
        <TeamMemberList teamMembers={teamData.members} />
      </div>
      {teamData.team.is_owner ? (
        <div className="flex-none">
          <h3>Find new team members</h3>
          <div className="mb-4 grid grid-flow-row gap-4">
            <SearchUsers
              currentMembers={teamData.members}
              searchResults={searchResults}
              setSearchResults={setSearchResults}
              user={user}
            />
            {searchResults.length > 0 &&
            searchResults.filter((u) => u.checked).length > 0 ? (
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
            ) : null}
          </div>
          <div className="w-48">
            <Button
              type="button"
              size="sm"
              icon="trash"
              onClick={() => setOpen(true)}
            >
              Delete team
            </Button>
            <Modal open={open} setOpen={setOpen}>
              <ConfirmationPopup
                title="Are you sure you want to delete this team?"
                content="Deleting this team will cause all team members to immediately lose access to any
projects, flights, and data associated with the team."
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
      ) : null}
    </div>
  );
}
