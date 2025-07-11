import { STACMetadata } from './STACTypes';
import { Project } from '../Project';

interface CollectionPreviewProps {
  stacMetadata: STACMetadata;
  project: Project;
}

export default function CollectionPreview({
  stacMetadata,
  project,
}: CollectionPreviewProps) {
  return (
    <div className="mb-4 p-3 bg-white rounded border border-gray-200 shadow-sm">
      <h4 className="font-semibold mb-2">Collection</h4>
      <div className="ml-4">
        <p>
          <span className="font-medium">Title:</span>{' '}
          {stacMetadata.collection.title}
        </p>
        <p>
          <span className="font-medium">Description:</span>{' '}
          {stacMetadata.collection.description}
        </p>
        {stacMetadata.collection['sci:doi'] && (
          <p>
            <span className="font-medium">DOI:</span>{' '}
            <a
              href={`https://doi.org/${stacMetadata.collection['sci:doi']}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline"
            >
              {stacMetadata.collection['sci:doi']}
            </a>
          </p>
        )}
        {stacMetadata.collection['sci:citation'] && (
          <p>
            <span className="font-medium">Citation:</span>{' '}
            {stacMetadata.collection['sci:citation']}
          </p>
        )}
        <p>
          <span className="font-medium">Spatial Extent:</span>{' '}
          {stacMetadata.collection.extent.spatial.bbox[0].join(', ')}
        </p>
        <p>
          <span className="font-medium">Temporal Extent:</span>{' '}
          {stacMetadata.collection.extent.temporal.interval[0].join(' to ')}
        </p>
        {stacMetadata.collection_url && project.is_published && (
          <p>
            <a
              href={stacMetadata.collection_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline"
            >
              View in STAC Browser (opens in new tab)
            </a>
          </p>
        )}
      </div>
    </div>
  );
}
