import { useState, useEffect, Dispatch, SetStateAction } from 'react';
import { AxiosResponse, isAxiosError } from 'axios';

import { fetchPotGroupModuleVisualizationData } from '../PotGroupModule/service';

import api from '../../../../../api';

import {
  IndoorProjectDataAPIResponse,
  IndoorProjectDataSpreadsheetAPIResponse,
  IndoorProjectDataVizAPIResponse,
  IndoorProjectDataViz2APIResponse,
  IndoorProjectDataVizScatterAPIResponse,
} from '../IndoorProject.d';

interface UseIndoorProjectDataProps {
  indoorProjectId: string;
}

interface UseIndoorProjectDataReturn {
  indoorProjectData: IndoorProjectDataAPIResponse[];
  indoorProjectDataSpreadsheet: IndoorProjectDataSpreadsheetAPIResponse | null;
  potModuleVisualizationData: IndoorProjectDataVizAPIResponse | null;
  potGroupModuleVisualizationData: IndoorProjectDataVizAPIResponse | null;
  traitModuleVisualizationData: IndoorProjectDataViz2APIResponse | null;
  traitScatterModuleVisualizationData: IndoorProjectDataVizScatterAPIResponse | null;
  isLoading: boolean;
  isLoadingData: boolean;
  error: { status: number; message: string } | null;
  setPotGroupModuleVisualizationData: Dispatch<
    SetStateAction<IndoorProjectDataVizAPIResponse | null>
  >;
  setTraitModuleVisualizationData: Dispatch<
    SetStateAction<IndoorProjectDataViz2APIResponse | null>
  >;
  setTraitScatterModuleVisualizationData: Dispatch<
    SetStateAction<IndoorProjectDataVizScatterAPIResponse | null>
  >;
  refetch: () => void;
}

export function useIndoorProjectData({
  indoorProjectId,
}: UseIndoorProjectDataProps): UseIndoorProjectDataReturn {
  const [indoorProjectData, setIndoorProjectData] = useState<
    IndoorProjectDataAPIResponse[]
  >([]);
  const [indoorProjectDataSpreadsheet, setIndoorProjectDataSpreadsheet] =
    useState<IndoorProjectDataSpreadsheetAPIResponse | null>(null);
  const [potModuleVisualizationData, setPotModuleVisualizationData] =
    useState<IndoorProjectDataVizAPIResponse | null>(null);
  const [potGroupModuleVisualizationData, setPotGroupModuleVisualizationData] =
    useState<IndoorProjectDataVizAPIResponse | null>(null);
  const [traitModuleVisualizationData, setTraitModuleVisualizationData] =
    useState<IndoorProjectDataViz2APIResponse | null>(null);
  const [
    traitScatterModuleVisualizationData,
    setTraitScatterModuleVisualizationData,
  ] = useState<IndoorProjectDataVizScatterAPIResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [error, setError] = useState<{
    status: number;
    message: string;
  } | null>(null);

  // Fetch uploaded data
  useEffect(() => {
    const fetchIndoorProjectData = async () => {
      try {
        const response: AxiosResponse<IndoorProjectDataAPIResponse[]> =
          await api.get(`/indoor_projects/${indoorProjectId}/uploaded`);
        setIndoorProjectData(response.data);
        setIsLoadingData(false);
      } catch (error) {
        if (isAxiosError(error)) {
          setError({
            status: error.response?.status || 500,
            message: `Failed to load uploaded data: ${
              error.response?.data?.message || error.message
            }`,
          });
        } else {
          setError({
            status: 500,
            message: 'An unexpected error occurred.',
          });
        }
        setIsLoadingData(false);
      }
    };

    if (indoorProjectId) {
      setIsLoadingData(true);
      fetchIndoorProjectData();
    }
  }, [indoorProjectId]);

  // Fetch spreadsheet data
  useEffect(() => {
    const fetchIndoorProjectSpreadsheet = async (
      indoorProjectDataId: string
    ) => {
      try {
        const response: AxiosResponse<IndoorProjectDataSpreadsheetAPIResponse> =
          await api.get(
            `/indoor_projects/${indoorProjectId}/uploaded/${indoorProjectDataId}`
          );
        setIndoorProjectDataSpreadsheet({
          records: response.data.records,
          summary: { id: indoorProjectDataId, ...response.data.summary },
          numeric_columns: response.data.numeric_columns,
        });
      } catch (error) {
        if (isAxiosError(error)) {
          setError({
            status: error.response?.status || 500,
            message: `Failed to load spreadsheet data: ${
              error.response?.data?.message || error.message
            }`,
          });
        } else {
          setError({
            status: 500,
            message: 'An unexpected error occurred.',
          });
        }
      }
    };

    const spreadsheets = indoorProjectData.filter(
      ({ file_type }) => file_type === '.xlsx'
    );
    if (spreadsheets.length > 0) {
      fetchIndoorProjectSpreadsheet(spreadsheets[0].id);
    }
  }, [indoorProjectId, indoorProjectData]);

  // Fetch visualization data
  useEffect(() => {
    let isMounted = true;

    async function loadVizData() {
      setError(null);
      setIsLoading(true);
      setPotModuleVisualizationData(null);

      const indoorProjectDataId = indoorProjectData.find(
        ({ file_type }) => file_type === '.xlsx'
      )?.id;

      if (!indoorProjectDataId) {
        setIsLoading(false);
        return;
      }

      try {
        const data = await fetchPotGroupModuleVisualizationData({
          indoorProjectId,
          indoorProjectDataId,
          cameraOrientation: 'side',
          plottedBy: 'pots',
          accordingTo: 'single_pot',
        });

        if (isMounted) {
          setPotModuleVisualizationData(data);
        }
      } catch (error) {
        if (isMounted) {
          setError({
            status: 500,
            message:
              error instanceof Error
                ? error.message
                : 'Failed to load visualization data',
          });
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadVizData();

    return () => {
      isMounted = false;
    };
  }, [indoorProjectId, indoorProjectData]);

  const refetch = () => {
    // Clear existing data and trigger a fresh fetch
    setIndoorProjectData([]);
    setIndoorProjectDataSpreadsheet(null);
    setPotModuleVisualizationData(null);
    setError(null);
    setIsLoadingData(true);

    // Trigger a re-fetch by updating a dependency
    const fetchIndoorProjectData = async () => {
      try {
        const response: AxiosResponse<IndoorProjectDataAPIResponse[]> =
          await api.get(`/indoor_projects/${indoorProjectId}/uploaded`);
        setIndoorProjectData(response.data);
        setIsLoadingData(false);
      } catch (error) {
        if (isAxiosError(error)) {
          setError({
            status: error.response?.status || 500,
            message: `Failed to load uploaded data: ${
              error.response?.data?.message || error.message
            }`,
          });
        } else {
          setError({
            status: 500,
            message: 'An unexpected error occurred.',
          });
        }
        setIsLoadingData(false);
      }
    };

    fetchIndoorProjectData();
  };

  return {
    indoorProjectData,
    indoorProjectDataSpreadsheet,
    potModuleVisualizationData,
    potGroupModuleVisualizationData,
    traitModuleVisualizationData,
    traitScatterModuleVisualizationData,
    isLoading,
    isLoadingData,
    error,
    setPotGroupModuleVisualizationData,
    setTraitModuleVisualizationData,
    setTraitScatterModuleVisualizationData,
    refetch,
  };
}
