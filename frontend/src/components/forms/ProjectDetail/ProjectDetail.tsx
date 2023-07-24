import axios from "axios";
import { useLoaderData, useNavigate } from "react-router-dom";

interface Project {
  id: string;
  title: string;
  description: string;
  planting_date: string;
  harvest_date: string;
}

export default function ProjectDetail() {
  const navigate = useNavigate();
  const project = useLoaderData() as Project;

  return (
    <div>
      <h2>{project.title}</h2>
      <button
        type="button"
        onClick={async () => {
          try {
            const data = { category: "UAS" };
            const response = await axios.post(
              `/api/v1/projects/${project.id}/datasets/`,
              data,
              {
                headers: {
                  Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
              }
            );

            if (response) {
              navigate(`/projects/${project.id}/datasets/${response.data.id}`);
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
        }}
      >
        Add Dataset
      </button>
      <pre>{JSON.stringify(project, undefined, 2)}</pre>
    </div>
  );
}
