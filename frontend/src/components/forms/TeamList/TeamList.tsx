import { useLoaderData, Link } from "react-router-dom";

interface Team {
  id: string;
  title: string;
  description: string;
}

export default function TeamList() {
  const teams = useLoaderData() as Team[];

  return (
    <div>
      {teams.length > 0 ? (
        <div>
          <h2>Teams</h2>
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Description</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {teams.map((team) => (
                <tr key={team.id}>
                  <td>{team.title}</td>
                  <td>{team.description}</td>
                  <td>A, B, C</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <em>No active teams</em>
      )}
      <div>
        <Link to="/teams/create">
          <button type="button" aria-label="Add Team">
            Add Team
          </button>
        </Link>
      </div>
    </div>
  );
}
