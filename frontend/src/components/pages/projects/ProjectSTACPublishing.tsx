import { isAxiosError } from 'axios';
import {
  GlobeAmericasIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';

import api from '../../../api';
import { confirm } from '../../ConfirmationDialog';

export default function ProjectSTACPublishing({
  is_published,
  projectId,
  setStatus,
}: {
  is_published: boolean;
  projectId: string;
  setStatus: (status: { type: string; msg: string }) => void;
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
      try {
        const response = await api.put(`/projects/${projectId}/publish-stac`);
        if (response) {
          setStatus({ type: 'success', msg: 'Project published to STAC' });
        }
      } catch (error) {
        if (isAxiosError(error)) {
          setStatus({ type: 'error', msg: error.response?.data.detail });
        } else {
          setStatus({
            type: 'error',
            msg: 'An error occurred while publishing the project to STAC',
          });
        }
      }
    }
  };

  const handleOnDelete = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (
      await confirm({
        title: 'Remove from STAC',
        description:
          'You are about to remove this project from the public STAC catalog. This action will make all data products associated with this project <strong>private</strong>.',
        confirmation: 'Are you sure you want to remove this project from STAC?',
      })
    ) {
      try {
        const response = await api.delete(`/projects/${projectId}/delete-stac`);
        if (response) {
          setStatus({ type: 'success', msg: 'Project removed from STAC' });
        }
      } catch (error) {
        if (isAxiosError(error)) {
          setStatus({ type: 'error', msg: error.response?.data.detail });
        } else {
          setStatus({
            type: 'error',
            msg: 'An error occurred while removing the project from STAC',
          });
        }
      }
    }
  };

  if (is_published) {
    return (
      <div className="flex flex-col items-center gap-2">
        <button
          className="w-32 flex flex-row items-center gap-2 py-0.5 px-2 border-2 rounded-md text-white ease-in-out duration-300 bg-[#4eb4ae] hover:bg-[#4eb4ae]/80 border-[#4eb4ae] hover:border-[#4eb4ae]/80"
          onClick={handleOnPublish}
        >
          <EyeIcon className="h-6 w-6" />
          <span className="text-sm font-semibold">Update</span>
        </button>
        <button
          className="w-32 flex flex-row items-center gap-2 py-0.5 px-2 border-2 rounded-md text-white ease-in-out duration-300 bg-red-600 hover:bg-red-700 border-red-600 hover:border-red-700"
          onClick={handleOnDelete}
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
