import { useLoaderData } from 'react-router-dom';

import TeamMemberList from '../TeamMemberList/TeamMemberList';

interface Team {
  id: string;
  title: string;
  description: string;
}

export default function TeamDetail() {
  const team = useLoaderData() as Team;
  return (
    <div>
      <div>
        <h2>{team.title}</h2>
        <span className="text-gray-600">{team.description}</span>
      </div>
      <hr className="mt-4 border-gray-700" />
      <div className="mt-9">
        <h2>{team.title} Members</h2>
        <TeamMemberList />
      </div>
    </div>
  );
}
