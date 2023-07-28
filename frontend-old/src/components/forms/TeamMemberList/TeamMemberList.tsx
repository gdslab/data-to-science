import { useEffect, useState } from "react";
import axios from "axios";

interface TeamMember {
  id: string;
  name: string;
}

export default function TeamMemberList() {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);

  useEffect(() => {
    async function fetchTeamMembers() {
      try {
        const teamID = 123;
        const response = await axios.get(`/api/v1/teams/${teamID}/members`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        });
        if (response) {
          setTeamMembers(response.data);
        } else {
          // do something
        }
      } catch (err) {
        if (axios.isAxiosError(err)) {
          console.error(err);
        } else {
          // do something
        }
      }
    }
    fetchTeamMembers();
  }, [teamMembers]);

  if (teamMembers.length < 1) {
    return <div>Add a team member</div>;
  } else {
    return (
      <table>
        <tr>
          <th>Name</th>
          <th>Actions</th>
        </tr>
        {teamMembers.map((teamMember) => (
          <tr>
            <th>{teamMember.name}</th>
            <th>X</th>
          </tr>
        ))}
      </table>
    );
  }
}
