import { useCallback } from 'react';
import { useRevalidator } from 'react-router-dom';
import api from '../../../../../api';
import { Status } from '../../../../Alert';

type ActionType = 'publish' | 'update' | 'unpublish';

interface ActionConfig {
  method: 'PUT' | 'DELETE';
  endpoint: (projectId: string, queryString?: string) => string;
  successMessage: string;
  errorMessage: string;
  operationType: 'publishing' | 'updating' | 'unpublishing';
}

interface UseSTACActionsProps {
  projectId: string;
  buildQueryParams: () => URLSearchParams;
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

export function useSTACActions({
  projectId,
  buildQueryParams,
  setCurrentOperation,
  setStatus,
}: UseSTACActionsProps): UseSTACActionsReturn {
  const revalidator = useRevalidator();

  const actionConfigs: Record<ActionType, ActionConfig> = {
    publish: {
      method: 'PUT',
      endpoint: (id, qs) =>
        `/projects/${id}/publish-stac-async${qs ? `?${qs}` : ''}`,
      successMessage:
        'Publish request sent. Please check back in a few minutes.',
      errorMessage: 'Failed to publish project',
      operationType: 'publishing',
    },
    update: {
      method: 'PUT',
      endpoint: (id, qs) =>
        `/projects/${id}/publish-stac-async${qs ? `?${qs}` : ''}`,
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

  const executeAction = useCallback(
    async (actionType: ActionType) => {
      const config = actionConfigs[actionType];

      setCurrentOperation(config.operationType);
      setStatus(null);

      try {
        const queryString =
          actionType !== 'unpublish' ? buildQueryParams().toString() : '';
        const endpoint = config.endpoint(projectId, queryString);

        if (config.method === 'PUT') {
          await api.put(endpoint);
        } else {
          await api.delete(endpoint);
        }

        setStatus({
          type: 'success',
          msg: config.successMessage,
        });
        revalidator.revalidate();
      } catch (err) {
        setStatus({
          type: 'error',
          msg: config.errorMessage,
        });
      } finally {
        setCurrentOperation('idle');
      }
    },
    [
      projectId,
      buildQueryParams,
      setCurrentOperation,
      setStatus,
      revalidator,
      actionConfigs,
    ]
  );

  return {
    handlePublish: () => executeAction('publish'),
    handleUpdate: () => executeAction('update'),
    handleUnpublish: () => executeAction('unpublish'),
  };
}
