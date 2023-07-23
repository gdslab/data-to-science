import { useEffect, useState } from "react";
import axios from "axios";

interface Team {
  title: string;
  description: string;
}

export default function TeamList() {
  const [teams, setTeams] = useState<Team[]>([]);

  useEffect(() => {
    async function fetchTeams() {
      try {
        const response = await axios.get("/api/v1/teams/", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        });
        if (response) {
          setTeams(response.data);
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
    fetchTeams();
  }, [teams]);

  if (teams.length < 1) {
    return <div>Create a team</div>;
  } else {
    return (
      <table>
        <tr>
          <th>Title</th>
          <th>Description</th>
          <th>Actions</th>
        </tr>
        {teams.map((team) => (
          <tr>
            <th>{team.title}</th>
            <th>{team.description}</th>
            <th>X</th>
          </tr>
        ))}
      </table>
    );
  }
}
