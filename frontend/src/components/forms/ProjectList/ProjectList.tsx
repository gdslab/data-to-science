import { useEffect, useState } from "react";
import axios from "axios";

interface Project {
  title: string;
  description: string;
}

export default function Project() {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    async function fetchProjects() {
      try {
        const response = await axios.get("/api/v1/projects/", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        });
        if (response) {
          setProjects(response.data);
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
    fetchProjects();
  }, [projects]);

  if (projects.length < 1) {
    return <div>Create a project</div>;
  } else {
    return (
      <table>
        <tr>
          <th>Title</th>
          <th>Description</th>
          <th>Actions</th>
        </tr>
        {projects.map((project) => (
          <tr>
            <th>{project.title}</th>
            <th>{project.description}</th>
            <th>X</th>
          </tr>
        ))}
      </table>
    );
  }
}
