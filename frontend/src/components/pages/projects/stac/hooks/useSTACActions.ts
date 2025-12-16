import { useCallback } from 'react';
import { useRevalidator } from 'react-router';
import api from '../../../../../api';
import { Status } from '../../../../Alert';
import { STACRequestPayload } from '../STACTypes';

type ActionType = 'publish' | 'update' | 'unpublish';

interface ActionConfig {
  method: 'PUT' | 'DELETE';
  endpoint: (projectId: string) => string;
  successMessage: string;
  errorMessage: string;
  operationType: 'publishing' | 'updating' | 'unpublishing';
}

interface UseSTACActionsProps {
  projectId: string;
  buildRequestPayload: () => STACRequestPayload;
  setCurrentOperation: (
    operation: 'idle' | 'publishing' | 'updating' | 'unpublishing'
  ) => void;
  setStatus: (status: Status | null) => void;
}

interface UseSTACActionsReturn {
  handlePublish: () => Promise<void>;
  handleUpdate: () => Promise<void>;
  handleUnpublish: () => Promise<void>;
}

const actionConfigs: Record<ActionType, ActionConfig> = {
  publish: {
    method: 'PUT',
    endpoint: (id) => `/projects/${id}/publish-stac-async`,
    successMessage:
      'Publish request sent. Please check back in a few minutes.',
    errorMessage: 'Failed to publish project',
    operationType: 'publishing',
  },
  update: {
    method: 'PUT',
    endpoint: (id) => `/projects/${id}/publish-stac-async`,
    successMessage:
      'Update request sent. Please check back in a few minutes.',
    errorMessage: 'Failed to update STAC catalog',
    operationType: 'updating',
  },
  unpublish: {
    method: 'DELETE',
    endpoint: (id) => `/projects/${id}/delete-stac`,
    successMessage: 'Project unpublished successfully',
    errorMessage: 'Failed to unpublish project',
    operationType: 'unpublishing',
  },
};

export function useSTACActions({
  projectId,
  buildRequestPayload,
  setCurrentOperation,
  setStatus,
}: UseSTACActionsProps): UseSTACActionsReturn {
  const revalidator = useRevalidator();

  const executeAction = useCallback(
    async (actionType: ActionType) => {
      const config = actionConfigs[actionType];

      setCurrentOperation(config.operationType);
      setStatus(null);

      try {
        const endpoint = config.endpoint(projectId);

        if (config.method === 'PUT') {
          const payload =
            actionType !== 'unpublish' ? buildRequestPayload() : {};
          await api.put(endpoint, payload);
        } else {
          await api.delete(endpoint);
        }

        setStatus({
          type: 'success',
          msg: config.successMessage,
        });
        revalidator.revalidate();
      } catch {
        setStatus({
          type: 'error',
          msg: config.errorMessage,
        });
      } finally {
        setCurrentOperation('idle');
      }
    },
    [projectId, buildRequestPayload, setCurrentOperation, setStatus, revalidator]
  );

  return {
    handlePublish: () => executeAction('publish'),
    handleUpdate: () => executeAction('update'),
    handleUnpublish: () => executeAction('unpublish'),
  };
}
