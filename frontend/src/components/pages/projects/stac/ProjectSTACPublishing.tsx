import { LoaderFunctionArgs, useLoaderData, useParams } from 'react-router-dom';

import { Project } from '../Project';
import { STACItem, STACMetadata } from './STACTypes';

// Custom hooks
import {
  useSTACOperations,
  useSTACForm,
  useSTACData,
  useSTACActions,
} from './hooks';

// UI Components
import {
  STACHeader,
  STACStatusIndicators,
  STACCustomizationPanel,
  STACPreviewPanel,
} from './components';

import api from '../../../../api';

export async function loader({ params }: LoaderFunctionArgs) {
  try {
    // First get the project to check if it's published
    const projectResponse = await api.get(`/projects/${params.projectId}`);
    const project = projectResponse.data;

    // Try to get cached STAC metadata first
    let stacMetadata = null;
    try {
      const cachedResponse = await api.get(
        `/projects/${params.projectId}/stac-cache`
      );
      stacMetadata = cachedResponse.data;
    } catch (cacheError) {
      // If no cache exists, generate preview asynchronously
      console.log('No cached STAC metadata found, will trigger generation');
    }

    return {
      stacMetadata,
      project: project,
    };
  } catch (error) {
    throw error;
  }
}

export default function ProjectSTACPublishing() {
  // Loader data
  const { stacMetadata: initialStacMetadata, project: loaderProject } =
    useLoaderData() as {
      stacMetadata: STACMetadata | null;
      project: Project;
    };
  const { projectId } = useParams();

  // Custom hooks for state management
  const operations = useSTACOperations();
  const formState = useSTACForm(initialStacMetadata);

  // STAC metadata management
  const { stacMetadata, allItems, generatePreview } = useSTACData({
    projectId: projectId!,
    initialStacMetadata,
    buildRequestPayload: formState.buildRequestPayload,
    setCurrentOperation: operations.setCurrentOperation,
    setStatus: operations.setStatus,
    setPollingStatus: operations.setPollingStatus,
  });

  // Action handlers
  const actions = useSTACActions({
    projectId: projectId!,
    buildRequestPayload: formState.buildRequestPayload,
    setCurrentOperation: operations.setCurrentOperation,
    setStatus: operations.setStatus,
  });

  return (
    <div className="p-4">
      <STACHeader />

      <STACStatusIndicators
        isGenerating={operations.isOperationActive('generating')}
        isChecking={operations.isOperationActive('checking')}
        stacMetadata={stacMetadata}
        pollingStatus={operations.pollingStatus}
        onRetry={generatePreview}
      />

      {/* Main content - only show if we have valid STAC metadata */}
      {stacMetadata && !('error' in stacMetadata) && (
        <div className="lg:grid lg:grid-cols-2 lg:gap-8">
          <STACCustomizationPanel
            project={loaderProject}
            formState={formState.formState}
            updateFormField={formState.updateFormField}
            stacItems={stacMetadata.items.filter(
              (item): item is STACItem => 'properties' in item
            )}
            actions={actions}
            operationStates={{
              isPublishing: operations.isOperationActive('publishing'),
              isUnpublishing: operations.isOperationActive('unpublishing'),
              isUpdating: operations.isOperationActive('updating'),
            }}
            status={operations.status}
          />

          <STACPreviewPanel
            stacMetadata={stacMetadata}
            allItems={allItems}
            project={loaderProject}
          />
        </div>
      )}
    </div>
  );
}
