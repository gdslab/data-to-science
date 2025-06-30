import { useState, useEffect } from 'react';
import {
  LoaderFunctionArgs,
  useLoaderData,
  useParams,
  useRevalidator,
} from 'react-router-dom';

import Alert, { Status } from '../../../Alert';
import { Project } from '../Project';
import ScientificCitationForm from './ScientificCitationForm';
import STACItemTitlesForm from './STACItemTitlesForm';
import { STACItem, STACMetadata, CombinedSTACItem } from './STACTypes';

import LoadingStatus from './LoadingStatus';
import ErrorDisplay from './ErrorDisplay';
import ActionButtons from './ActionButtons';
import CollectionPreview from './CollectionPreview';
import ProcessingSummary from './ProcessingSummary';
import ItemsList from './ItemsList';
import { usePolling } from '../../../hooks/usePolling';

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
  const [status, setStatus] = useState<Status | null>(null);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isUnpublishing, setIsUnpublishing] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [pollingStatus, setPollingStatus] = useState<string>('');
  const [sciDoi, setSciDoi] = useState<string>('');
  const [sciCitation, setSciCitation] = useState<string>('');
  const [license, setLicense] = useState<string>('CC-BY-NC-4.0');
  const [customTitles, setCustomTitles] = useState<Record<string, string>>({});
  const { stacMetadata: initialStacMetadata, project: loaderProject } =
    useLoaderData() as {
      stacMetadata: STACMetadata | null;
      project: Project;
    };
  const [stacMetadata, setStacMetadata] = useState<STACMetadata | null>(
    initialStacMetadata
  );
  const { projectId } = useParams();
  const revalidator = useRevalidator();

  // Helper function to combine successful and failed items for display
  const getAllItems = (): CombinedSTACItem[] => {
    if (!stacMetadata) return [];

    const allItems: CombinedSTACItem[] = [];

    // Add successful items - in preview mode, all items in the main array are successful
    stacMetadata.items.forEach((item) => {
      if ('properties' in item) {
        // This is a successful STAC item
        allItems.push({
          id: item.id,
          isSuccessful: true,
          title: item.properties.title,
          dataType: item.properties.data_product_details.data_type,
          acquisitionDate: item.properties.flight_details.acquisition_date,
          platform: item.properties.flight_details.platform,
          sensor: item.properties.flight_details.sensor,
          browserUrl: item.browser_url,
        });
      } else {
        // This is a failed item (ItemStatus) - should only happen in publish mode
        allItems.push({
          id: item.item_id,
          isSuccessful: false,
          error: item.error,
        });
      }
    });

    // Add failed items from the separate failed_items array (for preview mode)
    if (stacMetadata.failed_items) {
      stacMetadata.failed_items.forEach((failedItem) => {
        allItems.push({
          id: failedItem.item_id,
          isSuccessful: false,
          error: failedItem.error,
        });
      });
    }

    return allItems;
  };

  // Initialize form fields with existing values if published
  useEffect(() => {
    if (stacMetadata?.collection) {
      setSciDoi(stacMetadata.collection['sci:doi'] || '');
      setSciCitation(stacMetadata.collection['sci:citation'] || '');
      setLicense((stacMetadata.collection as any).license || 'CC-BY-NC-4.0');
    }
    // Initialize custom titles from STAC items if they have custom titles
    if (stacMetadata?.items) {
      const existingTitles: Record<string, string> = {};
      stacMetadata.items.forEach((item) => {
        // Check if this is a successful STAC item (has properties)
        if ('properties' in item && item.properties?.title) {
          // Check if it's a custom title (not the default format)
          const defaultTitlePattern =
            /^\d{4}-\d{2}-\d{2}_[\w\s]+_[\w\s]+_[\w\s]+$/;
          if (!defaultTitlePattern.test(item.properties.title)) {
            existingTitles[item.id] = item.properties.title;
          }
        }
      });
      setCustomTitles(existingTitles);
    }
  }, [stacMetadata]);

  // Use polling hook for STAC cache checking
  const { startPolling, stopPolling, isPolling } = usePolling({
    pollFunction: () => api.get(`/projects/${projectId}/stac-cache`),
    onSuccess: (response) => {
      setStacMetadata(response.data);
      setStatus({
        type: 'success',
        msg: 'STAC metadata generated successfully',
      });
    },
    onError: (_error) => {
      setStatus({
        type: 'error',
        msg: 'STAC generation is taking longer than expected. Please refresh the page to check status.',
      });
    },
    onProgress: setPollingStatus,
    maxAttempts: 30,
  });

  // Function to generate preview asynchronously
  const generatePreview = async () => {
    // Prevent multiple polling loops
    if (isPolling) {
      console.log('Polling already in progress, skipping...');
      return;
    }

    setIsGeneratingPreview(true);
    setStatus(null);

    try {
      const params = new URLSearchParams();
      if (sciDoi) params.append('sci_doi', sciDoi);
      if (sciCitation) params.append('sci_citation', sciCitation);
      if (license) params.append('license', license);
      if (customTitles && Object.keys(customTitles).length > 0) {
        params.append('custom_titles', JSON.stringify(customTitles));
      }
      const queryString = params.toString();

      // Start async generation
      await api.post(
        `/projects/${projectId}/generate-stac-preview${
          queryString ? `?${queryString}` : ''
        }`
      );

      // Start polling for results
      startPolling();
    } catch (err) {
      setStatus({
        type: 'error',
        msg: 'Failed to generate STAC metadata',
      });
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  // Check if we need to generate preview on component mount
  useEffect(() => {
    if (!stacMetadata && !isGeneratingPreview && !isPolling) {
      generatePreview();
    }
  }, [stacMetadata, isGeneratingPreview, isPolling]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  const buildPublishUrl = (
    doi?: string,
    citation?: string,
    license?: string,
    customTitles?: Record<string, string>
  ) => {
    const params = new URLSearchParams();
    if (doi) params.append('sci_doi', doi);
    if (citation) params.append('sci_citation', citation);
    if (license) params.append('license', license);
    if (customTitles && Object.keys(customTitles).length > 0) {
      params.append('custom_titles', JSON.stringify(customTitles));
    }
    const queryString = params.toString();
    return `/projects/${projectId}/publish-stac-async${
      queryString ? `?${queryString}` : ''
    }`;
  };

  const handlePublish = async () => {
    setIsPublishing(true);
    setStatus(null);
    try {
      const url = buildPublishUrl(sciDoi, sciCitation, license, customTitles);
      const response = await api.put(url);
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
    } finally {
      setIsPublishing(false);
    }
  };

  const handleUpdate = async () => {
    setIsUpdating(true);
    setStatus(null);
    try {
      const url = buildPublishUrl(sciDoi, sciCitation, license, customTitles);
      const response = await api.put(url);
      if (response) {
        setStatus({
          type: 'success',
          msg: 'STAC catalog updated successfully',
        });
        revalidator.revalidate();
      }
    } catch (err) {
      setStatus({
        type: 'error',
        msg: 'Failed to update STAC catalog',
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleUnpublish = async () => {
    setIsUnpublishing(true);
    setStatus(null);
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
    } finally {
      setIsUnpublishing(false);
    }
  };

  const allItems = getAllItems();

  return (
    <div className="p-4">
      <h2 className="text-lg font-bold mb-4">STAC Publishing</h2>

      <LoadingStatus
        isGeneratingPreview={isGeneratingPreview}
        stacMetadata={stacMetadata}
        pollingStatus={pollingStatus}
      />

      <ErrorDisplay stacMetadata={stacMetadata} onRetry={generatePreview} />

      {/* Main content - only show if we have valid STAC metadata */}
      {stacMetadata && !('error' in stacMetadata) && (
        <div className="lg:grid lg:grid-cols-2 lg:gap-8">
          {/* Left Column: Forms and Controls */}
          <div className="lg:col-span-1">
            <h3 className="text-md font-bold mb-4">Customization</h3>

            <ScientificCitationForm
              sciDoi={sciDoi}
              setSciDoi={setSciDoi}
              sciCitation={sciCitation}
              setSciCitation={setSciCitation}
              license={license}
              setLicense={setLicense}
            />

            <STACItemTitlesForm
              items={stacMetadata.items.filter(
                (item): item is STACItem => 'properties' in item
              )}
              customTitles={customTitles}
              setCustomTitles={setCustomTitles}
            />

            <ActionButtons
              project={loaderProject}
              isPublishing={isPublishing}
              isUnpublishing={isUnpublishing}
              isUpdating={isUpdating}
              onPublish={handlePublish}
              onUpdate={handleUpdate}
              onUnpublish={handleUnpublish}
            />

            {status && (
              <div className="mb-4">
                <Alert alertType={status.type}>{status.msg}</Alert>
              </div>
            )}
          </div>

          {/* Right Column: STAC Metadata Preview */}
          <div className="lg:col-span-1 mt-8 lg:mt-0">
            <h3 className="text-md font-bold mb-4">Metadata Preview</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <CollectionPreview stacMetadata={stacMetadata} />
              <ProcessingSummary allItems={allItems} />
              <ItemsList allItems={allItems} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
