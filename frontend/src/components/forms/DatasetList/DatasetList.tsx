import axios from 'axios';
import { useLoaderData, Link, Params } from 'react-router-dom';

import { Button } from '../CustomButtons';

interface Dataset {
  id: string;
  category: string;
  project_id: string;
}

export async function loader({ params }: { params: Params<string> }) {
  const response = await axios.get(`/api/v1/projects/${params.projectId}/datasets`);
  if (response) {
    const datasets = response.data;
    return datasets;
  } else {
    return [];
  }
}

export default function DatasetList() {
  const datasets = useLoaderData() as Dataset[];

  return (
    <div>
      {datasets.length > 0 ? (
        <div>
          <h2>Datasets</h2>
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((dataset) => (
                <tr key={dataset.id}>
                  <td>
                    <Link to={`/projects/${dataset.project_id}/datasets/${dataset.id}`}>
                      <Button>View {dataset.category}</Button>
                    </Link>
                  </td>
                  <td>X</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <em>No datasets</em>
      )}
    </div>
  );
}
