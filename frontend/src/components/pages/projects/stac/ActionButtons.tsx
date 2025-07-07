import { ArrowPathIcon } from '@heroicons/react/24/outline';
import { Button } from '../../../Buttons';
import { Project } from '../Project';

interface ActionButtonsProps {
  project: Project;
  isPublishing: boolean;
  isUnpublishing: boolean;
  isUpdating: boolean;
  onPublish: () => void;
  onUpdate: () => void;
  onUnpublish: () => void;
}

export default function ActionButtons({
  project,
  isPublishing,
  isUnpublishing,
  isUpdating,
  onPublish,
  onUpdate,
  onUnpublish,
}: ActionButtonsProps) {
  return (
    <div className="mb-4">
      <p className="text-gray-600 mb-2">
        Current status:{' '}
        <span className="font-semibold">
          {project?.is_published ? 'Published' : 'Not Published'}
        </span>
      </p>
      <div className="flex gap-4">
        {project?.is_published ? (
          <div className="flex gap-2">
            <Button onClick={onUpdate} color="blue" disabled={isUpdating}>
              {isUpdating ? (
                <div className="flex items-center">
                  <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                  Updating...
                </div>
              ) : (
                'Update Catalog'
              )}
            </Button>
            <Button onClick={onUnpublish} color="red" disabled={isUnpublishing}>
              {isUnpublishing ? (
                <div className="flex items-center">
                  <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                  Unpublishing...
                </div>
              ) : (
                'Unpublish'
              )}
            </Button>
          </div>
        ) : (
          <Button onClick={onPublish} color="blue" disabled={isPublishing}>
            {isPublishing ? (
              <div className="flex items-center">
                <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                Publishing...
              </div>
            ) : (
              'Publish'
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
