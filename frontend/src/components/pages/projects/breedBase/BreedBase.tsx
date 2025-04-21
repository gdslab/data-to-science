import axios, { AxiosResponse } from 'axios';
import { useEffect, useState } from 'react';
import { useForm, FormProvider, SubmitHandler } from 'react-hook-form';
import { useParams } from 'react-router-dom';
import { yupResolver } from '@hookform/resolvers/yup';

import BreedBaseStudies from './BreedBaseStudies';
import { TextInput } from '../../../RHFInputs';

import api from '../../../../api';
import {
  BreedBaseFormData,
  BreedBaseSearchAPIResponse,
  BreedBaseStudiesAPIResponse,
  BreedBaseStudy,
} from './BreedBase.types';
import defaultValues from './defaultValues';
import validationSchema from './validationSchema';

// Create a separate axios instance for BreedBase API calls without credentials
const breedBaseApi = axios.create({
  withCredentials: false,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default function BreedBase() {
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

  const { projectId } = useParams();

  useEffect(() => {
    const fetchBreedbaseStudies = async () => {
      const response: AxiosResponse<BreedBaseStudy[]> = await api.get(
        `/projects/${projectId}/breedbase`
      );
      setBreedbaseStudies(response.data);
    };
    fetchBreedbaseStudies();
  }, []);

  const methods = useForm<BreedBaseFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const {
    handleSubmit,
    formState: { errors },
  } = methods;

  const onSubmit: SubmitHandler<BreedBaseFormData> = async (data) => {
    setError(null);
    setIsLoading(true);

    try {
      // Split the search parameters into arrays
      const searchParams = {
        studyDbIds: data.studyDbIds
          ? data.studyDbIds.split(';').filter(Boolean)
          : [],
        studyNames: data.studyNames
          ? data.studyNames.split(';').filter(Boolean)
          : [],
        trialDbIds: data.trialDbIds
          ? data.trialDbIds.split(';').filter(Boolean)
          : [],
        trialNames: data.trialNames
          ? data.trialNames.split(';').filter(Boolean)
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
      if (axios.isAxiosError(err)) {
        if (err.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          setError(
            `Server error: ${
              err.response.data?.message || err.response.statusText
            }`
          );
        } else if (err.request) {
          // The request was made but no response was received
          setError(
            'No response received from server. Please check your connection.'
          );
        } else {
          // Something happened in setting up the request that triggered an Error
          setError(`Request error: ${err.message}`);
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setIsLoading(false);
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
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const onAddStudy = async (studyId: string) => {
    const breedBaseBaseUrl = methods.getValues('breedbaseUrl');
    if (!breedBaseBaseUrl) {
      setError('BreedBase URL is required');
      return;
    }

    try {
      const response: AxiosResponse<BreedBaseStudy> = await api.post(
        `/projects/${projectId}/breedbase`,
        {
          baseUrl: breedBaseBaseUrl,
          studyDbId: studyId,
        }
      );
      if (response.status === 200) {
        // Update the local state to include the new study
        setBreedbaseStudies((prev) => [...prev, response.data]);
      } else {
        setError('Failed to add study');
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(
          `Server error: ${
            err.response?.data?.message || err.response?.statusText
          }`
        );
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred');
      }
    }
  };

  return (
    <div className="h-full flex flex-col gap-4">
      <h2>BreedBase Connection</h2>
      <div className="flex flex-col gap-2">
        <div className="flex flex-col">
          <h3>Studies</h3>
          <p className="text-sm text-gray-500">
            Studies associated with this project.
          </p>
        </div>
        {breedbaseStudies.length > 0 ? (
          breedbaseStudies.map((study) => (
            <div key={study.id}>
              <div>{study.studyDbId}</div>
              <div>{study.baseUrl}</div>
            </div>
          ))
        ) : (
          <div>No studies found</div>
        )}
      </div>
      <hr className="border-t border-gray-400" />
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="flex flex-col">
            <h3>Search for studies</h3>
            <p className="text-sm text-gray-500">
              Search for studies to add to this project.
            </p>
          </div>
          <div className="flex flex-col gap-8">
            <TextInput
              fieldName="breedbaseUrl"
              label="BreedBase URL"
              placeholder="https://server/brapi/version"
            />
            <fieldset>
              <legend>Search Parameters (optional)</legend>
              <p className="text-sm text-gray-500">
                Separate multiple values with semicolons.
              </p>
              <div className="flex gap-2">
                <TextInput
                  fieldName="studyDbIds"
                  label="Study DB IDs"
                  placeholder="cf6c4bd4;691e69d6"
                />
                <TextInput
                  fieldName="studyNames"
                  label="Study Names"
                  placeholder="The First Bob Study 2017;Wheat Yield Trial 246"
                />
                <TextInput
                  fieldName="trialDbIds"
                  label="Trial DB IDs"
                  placeholder="d2593dc2;9431a731"
                />
                <TextInput
                  fieldName="trialNames"
                  label="Trial Names"
                  placeholder="All Yield Trials 2016;Disease Resistance Study Comparison Group"
                />
              </div>
            </fieldset>
            {error && <div className="text-red-500 text-sm">{error}</div>}
            <div>
              <button
                className="w-32 bg-accent2/90 text-white font-semibold py-1 rounded enabled:hover:bg-accent2 disabled:opacity-75 disabled:cursor-not-allowed"
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? 'Searching...' : 'Search Studies'}
              </button>
            </div>
          </div>
        </form>
      </FormProvider>
      {studiesApiResponse && (
        <BreedBaseStudies data={studiesApiResponse} onPageChange={fetchPage} />
      )}
    </div>
  );
}
