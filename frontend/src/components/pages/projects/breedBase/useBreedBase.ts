import { useState } from 'react';
import axios, { AxiosResponse } from 'axios';
import { UseFormReturn } from 'react-hook-form';

import {
  BreedBaseFormData,
  BreedBaseSearchAPIResponse,
  BreedBaseStudiesAPIResponse,
  BreedBaseStudy,
} from './BreedBase.types';

import api from '../../../../api';

// Create a separate axios instance for BreedBase API calls without credentials
const breedBaseApi = axios.create({
  withCredentials: false,
  headers: {
    'Content-Type': 'application/json',
  },
});

interface UseBreedBaseProps {
  projectId: string;
  methods: UseFormReturn<BreedBaseFormData>;
}

export function useBreedBase({ projectId, methods }: UseBreedBaseProps) {
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [breedbaseStudies, setBreedbaseStudies] = useState<BreedBaseStudy[]>(
    []
  );
  const [searchResultsDbId, setSearchResultsDbId] = useState<string | null>(
    null
  );
  const [studiesApiResponse, setStudiesApiResponse] =
    useState<BreedBaseStudiesAPIResponse | null>(null);

  const fetchBreedbaseStudies = async () => {
    try {
      const response: AxiosResponse<BreedBaseStudy[]> = await api.get(
        `/projects/${projectId}/breedbase-connections`
      );
      setBreedbaseStudies(response.data);
    } catch (err) {
      handleError(err);
    }
  };

  const handleError = (err: unknown) => {
    if (axios.isAxiosError(err)) {
      if (err.response) {
        setError(
          `Server error: ${
            err.response.data?.message || err.response.statusText
          }`
        );
      } else if (err.request) {
        setError(
          'No response received from server. Please check your connection.'
        );
      } else {
        setError(`Request error: ${err.message}`);
      }
    } else if (err instanceof Error) {
      setError(err.message);
    } else {
      setError('An unknown error occurred');
    }
  };

  const searchStudies = async (data: BreedBaseFormData) => {
    setError(null);
    setIsLoading(true);

    try {
      const searchParams = {
        studyDbIds: data.studyDbIds
          ? data.studyDbIds.split(';').filter(Boolean)
          : [],
        studyNames: data.studyNames
          ? data.studyNames.split(';').filter(Boolean)
          : [],
        programNames: data.programNames
          ? data.programNames.split(';').filter(Boolean)
          : [],
      };

      const searchResponse: AxiosResponse<BreedBaseSearchAPIResponse> =
        await breedBaseApi.post(
          `${data.breedbaseUrl}/search/studies`,
          searchParams
        );

      if (!searchResponse.data?.result?.searchResultsDbId) {
        throw new Error('Invalid search response: missing searchResultsDbId');
      }

      const searchResultsDbId = searchResponse.data.result.searchResultsDbId;
      setSearchResultsDbId(searchResultsDbId);

      const studiesResponse: AxiosResponse<BreedBaseStudiesAPIResponse> =
        await breedBaseApi.get(
          `${data.breedbaseUrl}/search/studies/${searchResultsDbId}`
        );

      if (!studiesResponse.data?.result?.data) {
        throw new Error('Invalid studies response: missing data');
      }
      setStudiesApiResponse(studiesResponse.data);
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const removeStudy = async (studyId: string) => {
    try {
      const response: AxiosResponse<BreedBaseStudy> = await api.delete(
        `/projects/${projectId}/breedbase-connections/${studyId}`
      );
      if (response.status === 200) {
        setBreedbaseStudies((prev) =>
          prev.filter((study) => study.id !== studyId)
        );
      } else {
        setError('Failed to remove study');
      }
    } catch (err) {
      handleError(err);
    }
  };

  const fetchPage = async (page: number) => {
    setError(null);
    setIsLoading(true);

    try {
      const formData = methods.getValues();
      const url = `${formData.breedbaseUrl}/search/studies/${searchResultsDbId}?page=${page}`;
      const response: AxiosResponse<BreedBaseStudiesAPIResponse> =
        await breedBaseApi.get(url);
      setStudiesApiResponse(response.data);
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const addStudy = async (studyId: string) => {
    const breedBaseBaseUrl = methods.getValues('breedbaseUrl');
    if (!breedBaseBaseUrl) {
      setError('BreedBase URL is required');
      return;
    }

    try {
      const response: AxiosResponse<BreedBaseStudy> = await api.post(
        `/projects/${projectId}/breedbase-connections`,
        {
          base_url: breedBaseBaseUrl,
          study_id: studyId,
        }
      );
      if (response.status === 201) {
        setBreedbaseStudies((prev) => [...prev, response.data]);
      } else {
        setError('Failed to add study');
      }
    } catch (err) {
      handleError(err);
    }
  };

  return {
    error,
    isLoading,
    breedbaseStudies,
    searchResultsDbId,
    studiesApiResponse,
    fetchBreedbaseStudies,
    searchStudies,
    removeStudy,
    fetchPage,
    addStudy,
  };
}
