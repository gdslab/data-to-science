import { AxiosResponse, isAxiosError } from 'axios';

import { Job } from '../../Project';

import { MetashapeSettings, ODMSettings } from './RawData.types';

import api from '../../../../../../api';

const checkForExistingJobs = async (
  flightId: string,
  projectId: string
): Promise<Job[]> => {
  try {
    const response: AxiosResponse<Job[]> = await api.get(
      `/projects/${projectId}/flights/${flightId}/check_progress`
    );
    if (response.status === 200) {
      return response.data;
    } else {
      return [];
    }
  } catch (err) {
    if (isAxiosError(err) && err.response && err.response.data.detail) {
      throw new Error(err.response.data.detail);
    } else {
      throw new Error('Unable to check for jobs');
    }
  }
};

const checkImageProcessingJobProgress = async (
  flightId: string,
  jobId: string,
  projectId: string,
  rawDataId: string
): Promise<number | null> => {
  try {
    const response: AxiosResponse<{ progress: string }> = await api.get(
      `/projects/${projectId}/flights/${flightId}/raw_data/${rawDataId}/check_progress/${jobId}`
    );
    if (response.status === 200) {
      return parseFloat(response.data.progress);
    } else {
      return null;
    }
  } catch (err) {
    if (isAxiosError(err) && err.response && err.response.data.detail) {
      throw err;
    } else {
      throw new Error('Unable to check for jobs');
    }
  }
};

const fetchUserExtensions = async (): Promise<'metashape' | 'odm' | null> => {
  try {
    const response: AxiosResponse<string[]> = await api.get(
      '/users/extensions'
    );
    if (response.status === 200 && Array.isArray(response.data)) {
      if (response.data.includes('metashape')) {
        return 'metashape';
      } else if (response.data.includes('odm')) {
        return 'odm';
      } else {
        return null;
      }
    } else {
      console.error('Invalid response format from extensions endpoint');
      return null;
    }
  } catch (err) {
    if (isAxiosError(err)) {
      if (err.response?.data?.detail) {
        throw new Error(
          `Failed to fetch user extensions: ${err.response.data.detail}`
        );
      }
      throw new Error(`Failed to fetch user extensions: ${err.message}`);
    }
    throw new Error('Failed to fetch user extensions: Unknown error occurred');
  }
};

const startImageProcessingJob = async (
  flightId: string,
  projectId: string,
  rawDataId: string,
  settings: MetashapeSettings | ODMSettings
): Promise<string> => {
  try {
    // convert number and boolean objects to string before creating query params
    const settingsStringParams: Record<string, string> = Object.keys(
      settings
    ).reduce((acc, key) => {
      acc[key] = String(settings[key]);
      return acc;
    }, {} as Record<string, string>);
    const settingsQueryString = new URLSearchParams(
      settingsStringParams
    ).toString();
    // send request to start job with user defined settings
    const response: AxiosResponse<{ job_id: string }> = await api.get(
      `/projects/${projectId}/flights/${flightId}/raw_data/${rawDataId}/process?${settingsQueryString}`
    );
    if (response.status === 200) {
      return response.data.job_id;
    } else {
      return '';
    }
  } catch (err) {
    if (isAxiosError(err) && err.response) {
      if (
        err.response.status === 422 &&
        Array.isArray(err.response.data.detail)
      ) {
        // Format Pydantic validation errors
        const validationErrors = err.response.data.detail
          .map((error: { loc: string[]; msg: string }) => {
            const field = error.loc[error.loc.length - 1];
            return `${field}: ${error.msg}`;
          })
          .join(', ');
        throw new Error(validationErrors);
      } else if (err.response.data.detail) {
        throw new Error(err.response.data.detail);
      } else {
        throw new Error('Unable to start job');
      }
    } else {
      throw new Error('Unable to start job');
    }
  }
};

export {
  checkForExistingJobs,
  checkImageProcessingJobProgress,
  fetchUserExtensions,
  startImageProcessingJob,
};
