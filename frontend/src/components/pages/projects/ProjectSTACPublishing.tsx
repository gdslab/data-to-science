import { useState } from 'react';
import {
  LoaderFunctionArgs,
  useLoaderData,
  useParams,
  useRevalidator,
} from 'react-router-dom';

import Alert, { Status } from '../../Alert';
import { Button } from '../../Buttons';
import LoadingBars from '../../LoadingBars';
import api from '../../../api';
import { useProjectContext } from './ProjectContext';
import { Project } from './Project';

interface STACMetadata {
  collection_id: string;
  collection: {
    id: string;
    title: string;
    description: string;
    extent: {
      spatial: {
        bbox: number[][];
      };
      temporal: {
        interval: string[][];
      };
    };
  };
  items: Array<{
    id: string;
    type: string;
    properties: {
      datetime: string;
      data_product_details: {
        data_type: string;
      };
      flight_details: {
        acquisition_date: string;
        platform: string;
        sensor: string;
      };
    };
    browser_url?: string;
  }>;
  is_published: boolean;
  collection_url?: string;
}

export async function loader({ params }: LoaderFunctionArgs) {
  try {
    // First get the project to check if it's published
    const projectResponse = await api.get(`/projects/${params.projectId}`);
    const project = projectResponse.data;

    let stacResponse;
    console.log(project);
    if (!project.is_published) {
      // If not published, get preview from our backend
      stacResponse = await api.put(
        `/projects/${params.projectId}/publish-stac?preview=true`
      );
    } else {
      // If published, get from STAC API
      stacResponse = await api.get(`/projects/${params.projectId}/stac`);
    }

    return {
      stacMetadata: stacResponse.data,
    };
  } catch (error) {
    throw error;
  }
}

export default function ProjectSTACPublishing() {
  const [status, setStatus] = useState<Status | null>(null);
  const { stacMetadata } = useLoaderData() as { stacMetadata: STACMetadata };
  const { project } = useProjectContext();
  const { projectId } = useParams();
  const revalidator = useRevalidator();

  const handlePublish = async () => {
    try {
      const response = await api.put(`/projects/${projectId}/publish-stac`);
      if (response) {
        setStatus({
          type: 'success',
          msg: 'Project published successfully',
        });
        revalidator.revalidate();
      }
    } catch (err) {
      setStatus({
        type: 'error',
        msg: 'Failed to publish project',
      });
    }
  };

  const handleUnpublish = async () => {
    try {
      const response = await api.delete(`/projects/${projectId}/delete-stac`);
      if (response) {
        setStatus({
          type: 'success',
          msg: 'Project unpublished successfully',
        });
        revalidator.revalidate();
      }
    } catch (err) {
      setStatus({
        type: 'error',
        msg: 'Failed to unpublish project',
      });
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-lg font-bold mb-4">STAC Publishing</h2>
      <div className="mb-4">
        <p className="text-gray-600 mb-2">
          Current status:{' '}
          <span className="font-semibold">
            {project?.is_published ? 'Published' : 'Not Published'}
          </span>
        </p>
        <div className="flex gap-4">
          {project?.is_published ? (
            <Button onClick={handleUnpublish} color="red">
              Unpublish
            </Button>
          ) : (
            <Button onClick={handlePublish} color="blue">
              Publish
            </Button>
          )}
        </div>
      </div>

      <div className="mt-8">
        <h3 className="text-md font-bold mb-4">STAC Metadata Preview</h3>
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold mb-2">Collection</h4>
          <div className="ml-4 mb-4 p-3 bg-white rounded border border-gray-200 shadow-sm">
            <p>
              <span className="font-medium">Title:</span>{' '}
              {stacMetadata.collection_url ? (
                <a
                  href={stacMetadata.collection_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  {stacMetadata.collection.title}
                </a>
              ) : (
                stacMetadata.collection.title
              )}
            </p>
            <p>
              <span className="font-medium">Description:</span>{' '}
              {stacMetadata.collection.description}
            </p>
            <p>
              <span className="font-medium">Spatial Extent:</span>{' '}
              {stacMetadata.collection.extent.spatial.bbox[0].join(', ')}
            </p>
            <p>
              <span className="font-medium">Temporal Extent:</span>{' '}
              {stacMetadata.collection.extent.temporal.interval[0].join(' to ')}
            </p>
          </div>

          <h4 className="font-semibold mb-2">
            Items ({stacMetadata.items.length})
          </h4>
          <div className="ml-4 max-h-96 overflow-y-auto">
            {stacMetadata.items.map((item) => (
              <div
                key={item.id}
                className="mb-2 p-2 bg-white rounded border border-gray-200 shadow-sm"
              >
                <p>
                  <span className="font-medium">ID:</span> {item.id}
                </p>
                {item.browser_url && (
                  <p>
                    <a
                      href={item.browser_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 underline"
                    >
                      STAC link
                    </a>
                  </p>
                )}
                <p>
                  <span className="font-medium">Data Type:</span>{' '}
                  {item.properties.data_product_details.data_type}
                </p>
                <p>
                  <span className="font-medium">Acquisition Date:</span>{' '}
                  {new Date(
                    item.properties.flight_details.acquisition_date
                  ).toLocaleDateString()}
                </p>
                <p>
                  <span className="font-medium">Platform:</span>{' '}
                  {item.properties.flight_details.platform.replace(/_/g, ' ')}
                </p>
                <p>
                  <span className="font-medium">Sensor:</span>{' '}
                  {item.properties.flight_details.sensor}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {status && <Alert alertType={status.type}>{status.msg}</Alert>}
    </div>
  );
}
