import { useState, useEffect, Dispatch, SetStateAction } from 'react';
import axios, { AxiosResponse, isAxiosError } from 'axios';
import {
  IndoorProjectDataAPIResponse,
  IndoorProjectDataSpreadsheetAPIResponse,
  IndoorProjectDataVizAPIResponse,
  IndoorProjectDataViz2APIResponse,
} from '../IndoorProject.d';
import { fetchPotGroupModuleVisualizationData } from '../PotGroupModule/service';

interface UseIndoorProjectDataProps {
  indoorProjectId: string;
}

interface UseIndoorProjectDataReturn {
  indoorProjectData: IndoorProjectDataAPIResponse[];
  indoorProjectDataSpreadsheet: IndoorProjectDataSpreadsheetAPIResponse | null;
  potModuleVisualizationData: IndoorProjectDataVizAPIResponse | null;
  potGroupModuleVisualizationData: IndoorProjectDataVizAPIResponse | null;
  traitModuleVisualizationData: IndoorProjectDataViz2APIResponse | null;
  isLoading: boolean;
  isLoadingData: boolean;
  error: { status: number; message: string } | null;
  setPotGroupModuleVisualizationData: Dispatch<
    SetStateAction<IndoorProjectDataVizAPIResponse | null>
  >;
  setTraitModuleVisualizationData: Dispatch<
    SetStateAction<IndoorProjectDataViz2APIResponse | null>
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
          await axios.get(
            `${
              import.meta.env.VITE_API_V1_STR
            }/indoor_projects/${indoorProjectId}/uploaded`
          );
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
          await axios.get(
            `${
              import.meta.env.VITE_API_V1_STR
            }/indoor_projects/${indoorProjectId}/uploaded/${indoorProjectDataId}`
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
  // useEffect(() => {
  //   let isMounted = true;

  //   async function loadVizData() {
  //     setError(null);
  //     setIsLoading(true);
  //     setPotModuleVisualizationData(null);

  //     const indoorProjectDataId = indoorProjectData.find(
  //       ({ file_type }) => file_type === '.xlsx'
  //     )?.id;

  //     if (!indoorProjectDataId) {
  //       setIsLoading(false);
  //       return;
  //     }

  //     try {
  //       const data = await fetchPotGroupModuleVisualizationData({
  //         indoorProjectId,
  //         indoorProjectDataId,
  //         cameraOrientation: 'side',
  //         groupBy: 'single_pot',
  //       });

  //       if (isMounted) {
  //         setPotModuleVisualizationData(data);
  //       }
  //     } catch (error) {
  //       if (isMounted) {
  //         setError({
  //           status: 500,
  //           message:
  //             error instanceof Error
  //               ? error.message
  //               : 'Failed to load visualization data',
  //         });
  //       }
  //     } finally {
  //       if (isMounted) {
  //         setIsLoading(false);
  //       }
  //     }
  //   }

  //   loadVizData();

  //   return () => {
  //     isMounted = false;
  //   };
  // }, [indoorProjectId, indoorProjectData]);

  const refetch = () => {
    console.log('running refetch');
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
          await axios.get(
            `${
              import.meta.env.VITE_API_V1_STR
            }/indoor_projects/${indoorProjectId}/uploaded`
          );
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
    isLoading,
    isLoadingData,
    error,
    setPotGroupModuleVisualizationData,
    setTraitModuleVisualizationData,
    refetch,
  };
}
