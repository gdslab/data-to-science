import axios from 'axios';
import { Link, useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { ArrowUpOnSquareIcon } from '@heroicons/react/24/outline';

import { Button } from '../CustomButtons';
import UploadModal from '../../UploadModal';

interface Dataset {
  id: string;
  category: string;
  project_id: string;
}

export default function DatasetList() {
  const { projectId } = useParams();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    async function fetchDatasets() {
      try {
        const response = await axios.get(`/api/v1/projects/${projectId}/datasets`);
        if (response) {
          setDatasets(response.data);
        } else {
          setDatasets([]);
        }
      } catch (err) {
        console.error(err);
      }
    }
    fetchDatasets();
  }, []);

  return (
    <div>
      {datasets.length > 0 ? (
        <div>
          {/* <h2>Datasets</h2>
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
          </table> */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
              <thead className="text-left">
                <tr>
                  <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                    Category
                  </th>
                  <th className="whitespace-nowrap px-4 py-2 font-medium text-center text-gray-900">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {datasets.map((dataset) => (
                  <tr key={dataset.id} className="odd:bg-gray-50">
                    <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                      {dataset.category}
                    </td>
                    <td className="flex items-center justify-around whitespace-nowrap px-4 py-2 text-gray-700">
                      <Link
                        to={`/projects/${projectId}/datasets/${dataset.id}`}
                        className="text-blue-600 font-bold italic"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <em>No datasets</em>
      )}
    </div>
  );
}
