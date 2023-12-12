import { Params } from 'react-router-dom';

export async function loader({ params }: { params: Params<string> }) {
  const { projectId } = params;
  // fetch team members associated with project

  return null;
}

export default function ProjectAccess() {
  // load team members with loader function

  return (
    <div className="p-4">
      <h1>Manage Access</h1>
    </div>
  );
}
