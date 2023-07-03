import { useEffect, useState } from "react";
import axios from "axios";

interface Project {
  title: string;
  description: string;
  location: object;
  planting_date: Date;
  harvest_date: Date;
}

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);

  async function getProjects() {
    try {
      const response = await axios.get("/api/v1/projects", {
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
        // do something
      } else {
        // do something
      }
    }
  }

  return (
    <div style={{ width: 450 }}>
      <fieldset>
        <legend>My Projects</legend>
        <button onClick={() => getProjects()}>Get projects</button>
        {projects.length > 0 ? (
          <pre>{JSON.stringify(projects, undefined, 2)}</pre>
        ) : (
          <div>Add a project</div>
        )}
      </fieldset>
    </div>
  );
}
