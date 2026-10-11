import { useState, useCallback, useRef } from 'react';
import axios, { AxiosResponse } from 'axios';
import { UseFormReturn } from 'react-hook-form';

import {
  BreedBaseFormData,
  BreedBaseSearchAPIResponse,
  BreedBaseStudiesAPIResponse,
  BreedBaseStudy,
} from './BreedBase.types';

import api from '../../../../../api';

interface UseBreedBaseProps {
  projectId: string;
  methods: UseFormReturn<BreedBaseFormData>;
  getAuthToken?: (hostname: string) => string | null;
  onAuthExpired?: (breedbaseUrl: string) => void;
}

function getAccessToken(
  url: string,
  getAuthToken?: (hostname: string) => string | null
): string | undefined {
  if (!getAuthToken) return undefined;
  try {
    const hostname = new URL(url).hostname;
    return getAuthToken(hostname) || undefined;
  } catch {
    return undefined;
  }
}

export function useBreedBase({ projectId, methods, getAuthToken, onAuthExpired }: UseBreedBaseProps) {
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
  const [studyDetails, setStudyDetails] = useState<
    Record<string, { studyName: string; seasons: string }>
  >({});
  const [loadingStudyDetails, setLoadingStudyDetails] = useState<
    Record<string, boolean>
  >({});
  const fetchedStudyKeysRef = useRef<Set<string>>(new Set());

  const fetchBreedbaseStudies = useCallback(async () => {
    try {
      const response: AxiosResponse<BreedBaseStudy[]> = await api.get(
        `/projects/${projectId}/breedbase-connections`
      );
      setBreedbaseStudies(response.data);
    } catch (err) {
      handleError(err);
    }
  }, [projectId]);

  const handleError = (err: unknown, isProxyRequest = false) => {
    if (axios.isAxiosError(err)) {
      if (isProxyRequest && err.response?.status === 401) {
        const url = methods.getValues('breedbaseUrl');
        onAuthExpired?.(url);
        setError('Session expired. Please log in again.');
        return;
      }
      if (err.response) {
        setError(
          `Server error: ${
            err.response.data?.detail || err.response.data?.message || err.response.statusText
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

  const brapiProxy = async (
    url: string,
    method: 'GET' | 'POST' = 'GET',
    body?: Record<string, unknown>
  ) => {
    const access_token = getAccessToken(url, getAuthToken);
    const response = await api.post('/breedbase/brapi/proxy', {
      url,
      method,
      body: body || null,
      brapi_token: access_token || null,
    });
    return response;
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
        seasonDbIds: data.year ? data.year.split(';').filter(Boolean) : [],
      };

      const searchResponse = await brapiProxy(
        `${data.breedbaseUrl}/search/studies`,
        'POST',
        searchParams
      );

      const searchData = searchResponse.data as BreedBaseSearchAPIResponse;
      if (!searchData?.result?.searchResultsDbId) {
        throw new Error('Invalid search response: missing searchResultsDbId');
      }

      const searchResultsDbId = searchData.result.searchResultsDbId;
      setSearchResultsDbId(searchResultsDbId);

      const studiesResponse = await brapiProxy(
        `${data.breedbaseUrl}/search/studies/${searchResultsDbId}`
      );

      const studiesData = studiesResponse.data as BreedBaseStudiesAPIResponse;
      if (!studiesData?.result?.data) {
        throw new Error('Invalid studies response: missing data');
      }
      setStudiesApiResponse(studiesData);
    } catch (err) {
      handleError(err, true);
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
      const response = await brapiProxy(
        `${formData.breedbaseUrl}/search/studies/${searchResultsDbId}?page=${page}`
      );
      setStudiesApiResponse(response.data as BreedBaseStudiesAPIResponse);
    } catch (err) {
      handleError(err, true);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStudyDetails = useCallback(
    async (baseUrl: string, studyId: string) => {
      const studyKey = `${baseUrl}-${studyId}`;

      // Skip if already fetched or in-flight
      if (fetchedStudyKeysRef.current.has(studyKey)) {
        return;
      }
      fetchedStudyKeysRef.current.add(studyKey);

      setLoadingStudyDetails((prev) => ({ ...prev, [studyKey]: true }));

      try {
        const response = await brapiProxy(
          `${baseUrl}/studies/${studyId}`
        );
        if (response.status === 200 && response.data?.result) {
          const studyName =
            response.data.result.studyName || 'Unknown Study';
          const seasons = response.data.result.seasons
            ? response.data.result.seasons.join(', ')
            : 'N/A';
          setStudyDetails((prev) => ({
            ...prev,
            [studyKey]: { studyName, seasons },
          }));
        } else {
          setStudyDetails((prev) => ({
            ...prev,
            [studyKey]: {
              studyName: 'Error loading details',
              seasons: 'N/A',
            },
          }));
        }
      } catch (err) {
        console.error('Error fetching study details:', err);
        setStudyDetails((prev) => ({
          ...prev,
          [studyKey]: {
            studyName: 'Error loading details',
            seasons: 'N/A',
          },
        }));
      } finally {
        setLoadingStudyDetails((prev) => ({ ...prev, [studyKey]: false }));
      }
    },
    [getAuthToken]
  );

  const refreshStudyDetails = useCallback(() => {
    fetchedStudyKeysRef.current.clear();
    setStudyDetails({});
    breedbaseStudies.forEach((study) => {
      fetchStudyDetails(study.base_url, study.study_id);
    });
  }, [breedbaseStudies, fetchStudyDetails]);

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
    studyDetails,
    loadingStudyDetails,
    fetchBreedbaseStudies,
    searchStudies,
    removeStudy,
    fetchPage,
    addStudy,
    fetchStudyDetails,
    refreshStudyDetails,
  };
}
