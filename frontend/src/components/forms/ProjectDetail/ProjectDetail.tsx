import axios from 'axios';
import { Params, useLoaderData, useNavigate } from 'react-router-dom';

import { CustomButton } from '../CustomButtons';
import ProjectForm from '../ProjectForm';

interface Project {
  id: string;
  title: string;
  description: string;
  planting_date: string;
  harvest_date: string;
  location_id: string;
  team_id: string;
}

export async function loader({ params }: { params: Params<string> }) {
  const response = await axios.get(`/api/v1/projects/${params.projectId}`);
  if (response) {
    return response.data;
  } else {
    return null;
  }
}

export default function ProjectDetail() {
  const navigate = useNavigate();
  const project = useLoaderData() as Project;
  const datasets = [];
  const storedValues = {
    title: project.title,
    description: project.description,
    locationId: project.location_id,
    plantingDate: project.planting_date,
    harvestDate: project.harvest_date ? project.harvest_date : '',
    teamId: project.team_id ? project.team_id : '',
  };
  return (
    <div className="m-4">
      <div>
        <h2>{project.title}</h2>
        <span className="text-gray-600">{project.description}</span>
      </div>
      <div>
        <ProjectForm
          editMode={true}
          projectId={project.id}
          storedValues={storedValues}
        />
      </div>
      <div className="m-4">
        <h1>Datasets</h1>
        <div>
          {datasets.length < 1 ? <em>No datasets associated with project</em> : null}
        </div>
        <div className="mt-4" style={{ width: 450 }}>
          <CustomButton
            onClick={async () => {
              try {
                const data = { category: 'UAS' };
                const response = await axios.post(
                  `/api/v1/projects/${project.id}/datasets/`,
                  data
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
          </CustomButton>
        </div>
      </div>
    </div>
  );
}
