import {
  GlobeAmericasIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';

import { confirm } from '../../ConfirmationDialog';

export default function ProjectSTACPublishing({
  is_published,
  projectId,
}: {
  is_published: boolean;
  projectId: string;
}) {
  const handleOnPublish = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (
      await confirm({
        title: 'Publish to STAC',
        description:
          'You are about to publish this project to a public STAC catalog. This action will make all data products associated with this project <strong>publicly available</strong>.',
        confirmation: 'Are you sure you want to publish this project to STAC?',
      })
    ) {
      console.log('publish');
    }
  };

  const handleOnUpdate = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (
      await confirm({
        title: 'Update on STAC',
        description:
          'You are about to update this project on a public STAC catalog. This action will make all data products associated with this project <strong>publicly available</strong>.',
        confirmation: 'Are you sure you want to update this project on STAC?',
      })
    ) {
      console.log('update');
    }
  };
  if (is_published) {
    return (
      <div className="flex flex-col items-center gap-2">
        <button
          className="w-32 flex flex-row items-center gap-2 py-0.5 px-2 border-2 rounded-md text-white ease-in-out duration-300 bg-[#4eb4ae] hover:bg-[#4eb4ae]/80 border-[#4eb4ae] hover:border-[#4eb4ae]/80"
          onClick={handleOnUpdate}
        >
          <EyeIcon className="h-6 w-6" />
          <span className="text-sm font-semibold">Update</span>
        </button>
        <button
          className="w-32 flex flex-row items-center gap-2 py-0.5 px-2 border-2 rounded-md text-white ease-in-out duration-300 bg-red-600 hover:bg-red-700 border-red-600 hover:border-red-700"
          onClick={handleOnUpdate}
        >
          <EyeSlashIcon className="h-6 w-6" />
          <span className="text-sm font-semibold">Unpublish</span>
        </button>
      </div>
    );
  } else {
    return (
      <button
        className="w-32 flex flex-row items-center gap-2 py-0.5 px-2 border-2 rounded-md text-white ease-in-out duration-300 bg-[#4eb4ae] hover:bg-[#4eb4ae]/80 border-[#4eb4ae] hover:border-[#4eb4ae]/80"
        onClick={handleOnPublish}
      >
        <GlobeAmericasIcon className="h-6 w-6" />
        <span className="text-sm font-semibold">Publish</span>
      </button>
    );
  }
}
