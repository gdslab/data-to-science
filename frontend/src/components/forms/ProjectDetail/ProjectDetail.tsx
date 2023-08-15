import axios from 'axios';
import { Link, Params, useLoaderData, useNavigate } from 'react-router-dom';

import { Button } from '../CustomButtons';
import DatasetList from '../DatasetList/DatasetList';

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

  return (
    <div className="">
      <div className="m-4">
        <h1>Datasets</h1>
        <div>
          {datasets.length < 1 ? <em>No datasets associated with project</em> : null}
        </div>
        <div className="mt-4" style={{ width: 450 }}>
          <Button
            onClick={async () => {
              try {
                const data = { category: 'UAS' };
                const response = await axios.post(
                  `/api/v1/projects/${project.id}/datasets/`,
                  data
                );

                if (response) {
                  navigate(
                    `/projects/${project.id}/datasets/${response.data.id}/create`
                  );
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
            Add Flight
          </Button>
        </div>
        <div className="mt-4" style={{ width: 450 }}>
          <DatasetList />
        </div>
      </div>
    </div>
  );
}
