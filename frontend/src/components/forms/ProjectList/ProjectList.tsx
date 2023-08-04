import axios from 'axios';
import { useLoaderData, Link } from 'react-router-dom';

interface Project {
  id: string;
  title: string;
  description: string;
}

export async function loader() {
  const response = await axios.get('/api/v1/projects/');
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

export default function ProjectList() {
  const projects = useLoaderData() as Project[];

  return (
    <div>
      {projects.length > 0 ? (
        <div>
          <h2>Projects</h2>
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Description</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id}>
                  <td>
                    <Link to={`/projects/${project.id}`}>{project.title}</Link>
                  </td>
                  <td>{project.description}</td>
                  <td>X</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <em>No active projects</em>
      )}
      <div>
        <Link to="/projects/create">
          <button type="button" aria-label="Add Project">
            Add Project
          </button>
        </Link>
      </div>
    </div>
  );
}
