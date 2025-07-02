import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { STACMetadata, CombinedSTACItem } from '../STACTypes';
import { usePolling } from '../../../../hooks/usePolling';
import { Status } from '../../../../Alert';
import api from '../../../../../api';

interface UseSTACDataProps {
  projectId: string;
  initialStacMetadata: STACMetadata | null;
  buildQueryParams: () => URLSearchParams;
  setCurrentOperation: (operation: 'idle' | 'generating' | 'checking') => void;
  setStatus: (status: Status | null) => void;
  setPollingStatus: (status: string) => void;
}

interface UseSTACDataReturn {
  stacMetadata: STACMetadata | null;
  allItems: CombinedSTACItem[];
  generatePreview: () => void;
  checkForUpdates: () => void;
}

export function useSTACData({
  projectId,
  initialStacMetadata,
  buildQueryParams,
  setCurrentOperation,
  setStatus,
  setPollingStatus,
}: UseSTACDataProps): UseSTACDataReturn {
  const [stacMetadata, setStacMetadata] = useState<STACMetadata | null>(
    initialStacMetadata
  );
  const hasCheckedForUpdates = useRef(false);
  const isBackgroundPolling = useRef(false);

  // Helper function to detect meaningful metadata changes
  const hasMetadataChanged = useCallback(
    (oldData: any, newData: any): boolean => {
      if (!oldData && newData) return true;
      if (oldData && !newData) return true;
      if (!oldData && !newData) return false;

      const oldHasError = 'error' in oldData;
      const newHasError = 'error' in newData;
      if (oldHasError !== newHasError) return true;

      if (oldHasError && newHasError) {
        return oldData.error !== newData.error;
      }

      if (!oldHasError && !newHasError) {
        if (oldData.collection?.timestamp !== newData.collection?.timestamp)
          return true;
        if (oldData.items?.length !== newData.items?.length) return true;
        if (oldData.failed_items?.length !== newData.failed_items?.length)
          return true;

        if (oldData.items && newData.items) {
          const oldIds = oldData.items
            .map((item: any) => ('properties' in item ? item.id : item.item_id))
            .sort();
          const newIds = newData.items
            .map((item: any) => ('properties' in item ? item.id : item.item_id))
            .sort();
          return JSON.stringify(oldIds) !== JSON.stringify(newIds);
        }
      }

      return false;
    },
    []
  );

  // Transform items for display
  const allItems = useMemo((): CombinedSTACItem[] => {
    if (!stacMetadata || 'error' in stacMetadata) return [];

    const items: CombinedSTACItem[] = [];

    // Add successful items
    stacMetadata.items.forEach((item) => {
      if ('properties' in item) {
        items.push({
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
        items.push({
          id: item.item_id,
          isSuccessful: false,
          error: item.error,
        });
      }
    });

    // Add failed items from separate array
    if (stacMetadata.failed_items) {
      stacMetadata.failed_items.forEach((failedItem) => {
        items.push({
          id: failedItem.item_id,
          isSuccessful: false,
          error: failedItem.error,
        });
      });
    }

    return items;
  }, [stacMetadata]);

  // Polling hook for STAC cache checking
  const { startPolling, stopPolling, isPolling } = usePolling({
    pollFunction: () => api.get(`/projects/${projectId}/stac-cache`),
    onSuccess: (response) => {
      const freshData = response.data;

      if (isBackgroundPolling.current) {
        // Background check - only update if there are changes
        if (hasMetadataChanged(stacMetadata, freshData)) {
          setStacMetadata(freshData);

          const hasError = stacMetadata && 'error' in stacMetadata;
          const freshHasError = 'error' in freshData;

          if (hasError && !freshHasError) {
            setStatus({
              type: 'success',
              msg: 'STAC metadata is now available for publishing',
            });
          } else if (!hasError && freshHasError) {
            setStatus({
              type: 'info',
              msg: 'Project status has changed',
            });
          }
        }
        isBackgroundPolling.current = false;
      } else {
        // Regular generation - always update
        setStacMetadata(freshData);
        setStatus({
          type: 'success',
          msg: 'STAC metadata generated successfully',
        });
      }

      setCurrentOperation('idle');
    },
    onError: (_error) => {
      isBackgroundPolling.current = false;
      setCurrentOperation('idle');
      setStatus({
        type: 'error',
        msg: 'STAC generation is taking longer than expected. Please refresh the page to check status.',
      });
    },
    onProgress: setPollingStatus,
    maxAttempts: 30,
  });

  // Main metadata refresh function
  const refreshMetadata = useCallback(
    async (
      options: { isBackgroundCheck?: boolean; usePolling?: boolean } = {}
    ) => {
      const { isBackgroundCheck = false, usePolling = false } = options;

      // Prevent concurrent operations
      if (isPolling) {
        console.log('STAC operation already in progress, skipping...');
        return;
      }

      setCurrentOperation(isBackgroundCheck ? 'checking' : 'generating');

      if (!isBackgroundCheck) {
        setStatus(null);
      }

      try {
        const queryString = buildQueryParams().toString();
        await api.post(
          `/projects/${projectId}/generate-stac-preview${
            queryString ? `?${queryString}` : ''
          }`
        );

        if (usePolling || isBackgroundCheck) {
          if (isBackgroundCheck) {
            isBackgroundPolling.current = true;
          }
          startPolling();
        } else {
          // Direct fetch for immediate results
          const response = await api.get(`/projects/${projectId}/stac-cache`);
          setStacMetadata(response.data);
          setStatus({
            type: 'success',
            msg: 'STAC metadata generated successfully',
          });
          setCurrentOperation('idle');
        }
      } catch (err) {
        if (isBackgroundCheck) {
          console.log('Background STAC check failed:', err);
        } else {
          setStatus({
            type: 'error',
            msg: 'Failed to generate STAC metadata',
          });
        }
        setCurrentOperation('idle');
      }
    },
    [
      projectId,
      buildQueryParams,
      setCurrentOperation,
      setStatus,
      isPolling,
      startPolling,
    ]
  );

  // Convenience methods
  const generatePreview = useCallback(
    () => refreshMetadata({ usePolling: true }),
    [refreshMetadata]
  );

  const checkForUpdates = useCallback(
    () => refreshMetadata({ isBackgroundCheck: true }),
    [refreshMetadata]
  );

  // Initial data loading effect
  useEffect(() => {
    hasCheckedForUpdates.current = false;

    if (!initialStacMetadata) {
      generatePreview();
    } else {
      hasCheckedForUpdates.current = true;
      checkForUpdates();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup effect
  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  return {
    stacMetadata,
    allItems,
    generatePreview,
    checkForUpdates,
  };
}
