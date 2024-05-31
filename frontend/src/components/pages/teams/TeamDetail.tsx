import axios from 'axios';
import { Formik, Form } from 'formik';
import { useContext, useState } from 'react';
import { Params, useLoaderData, useNavigate, useRevalidator } from 'react-router-dom';

import AuthContext from '../../../AuthContext';
import { Button } from '../../Buttons';
import { ConfirmationPopup } from '../../ConfirmationPopup';
import { Editing, EditField, TextField } from '../../InputFields';
import Modal from '../../Modal';
import TeamMemberList from './TeamMemberList';

import validationSchema from './validationSchema';
import SearchUsers, { UserSearch } from './SearchUsers';

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
    const teamResponse = await axios.get(`/api/v1/teams/${params.teamId}`);
    const teamMembers = await axios.get(`/api/v1/teams/${params.teamId}/members`);
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
  const [isEditing, setIsEditing] = useState<Editing>(null);
  const [searchResults, setSearchResults] = useState<UserSearch[]>([]);

  return (
    <div>
      {teamData.team.is_owner ? (
        <Formik
          initialValues={{
            title: teamData.team.title,
            description: teamData.team.description,
          }}
          validationSchema={validationSchema}
          onSubmit={async (values) => {
            try {
              const response = await axios.put(
                `/api/v1/teams/${teamData.team.id}`,
                values
              );
              if (response) {
                revalidator.revalidate();
              }
              setIsEditing(null);
            } catch (err) {
              setIsEditing(null);
            }
          }}
        >
          {() => (
            <Form>
              <div className="grid rows-auto gap-2">
                <EditField
                  fieldName="title"
                  isEditing={isEditing}
                  setIsEditing={setIsEditing}
                >
                  {!isEditing || isEditing.field !== 'title' ? (
                    <h2 className="mb-0">{teamData.team.title}</h2>
                  ) : (
                    <TextField name="title" />
                  )}
                </EditField>
                <EditField
                  fieldName="description"
                  isEditing={isEditing}
                  setIsEditing={setIsEditing}
                >
                  {!isEditing || isEditing.field !== 'description' ? (
                    <span className="text-gray-600">{teamData.team.description}</span>
                  ) : (
                    <TextField name="description" />
                  )}
                </EditField>
              </div>
            </Form>
          )}
        </Formik>
      ) : (
        <div className="grid rows-auto gap-2">
          <h2 className="mb-0">{teamData.team.title}</h2>
          <span className="text-gray-600">{teamData.team.description}</span>
        </div>
      )}
      <hr className="mt-4 border-gray-700" />
      <div className="mt-9">
        <h2>{teamData.team.title} Members</h2>
        <TeamMemberList teamMembers={teamData.members} />
      </div>
      {teamData.team.is_owner ? (
        <div className="mt-4">
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
                  const selectedMembers = searchResults.filter((u) => u.checked);
                  if (selectedMembers.length > 0) {
                    axios
                      .post(
                        `/api/v1/teams/${teamData.team.id}/members/multi`,
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
            <Button type="button" size="sm" icon="trash" onClick={() => setOpen(true)}>
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
                    const response = await axios.delete(
                      `/api/v1/teams/${teamData.team.id}`
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
