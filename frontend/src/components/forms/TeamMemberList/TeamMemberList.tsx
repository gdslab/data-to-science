import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

interface TeamMember {
  id: string;
  full_name: string;
  email: string;
}

export default function TeamMemberList() {
  const { teamId } = useParams();
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  useEffect(() => {
    async function fetchTeamMembers() {
      try {
        const response = await axios.get(`/api/v1/teams/${teamId}/members`);
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
  }, []);
  if (teamMembers.length < 1) {
    return <div>No team members</div>;
  } else {
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
          <thead className="text-left">
            <tr>
              <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                Name
              </th>
              <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                Email
              </th>
              <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                Role
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-200">
            {teamMembers.map((teamMember) => (
              <tr key={teamMember.id} className="odd:bg-gray-50">
                <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                  {teamMember.full_name}
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                  {teamMember.email}
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-gray-700">Member</td>
              </tr>
            ))}
            <tr className="odd:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                John Doe
              </td>
              <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                johndoe@example.com
              </td>
              <td className="whitespace-nowrap px-4 py-2 text-gray-700">Member</td>
            </tr>

            <tr className="odd:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                Jane Doe
              </td>
              <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                janedoe@example.com
              </td>
              <td className="whitespace-nowrap px-4 py-2 text-gray-700">Member</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }
}
