import { AxiosResponse, isAxiosError } from 'axios';

import { Job } from '../../Project';

import {
  ImageProcessingBackend,
  MetashapeSettings,
  ODMSettings,
  ProcessingJob,
} from './RawData.types';

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

const fetchRawDataProcessingJobs = async (
  projectId: string,
  flightId: string,
  rawDataId: string
): Promise<ProcessingJob[]> => {
  try {
    const response: AxiosResponse<ProcessingJob[]> = await api.get(
      `/projects/${projectId}/flights/${flightId}/raw_data/${rawDataId}/jobs`,
      { params: { name: 'processing-raw-data' } }
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
      throw new Error('Unable to fetch processing history');
    }
  }
};

const fetchUserExtensions = async (): Promise<ImageProcessingBackend[]> => {
  try {
    const response: AxiosResponse<string[]> = await api.get(
      '/users/extensions'
    );
    if (response.status === 200 && Array.isArray(response.data)) {
      // metashape listed first so it remains the default backend
      return (['metashape', 'odm'] as ImageProcessingBackend[]).filter((ext) =>
        response.data.includes(ext)
      );
    } else {
      console.error('Invalid response format from extensions endpoint');
      return [];
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

const formatSettingKey = (key: string): string =>
  key
    .replace(/([a-z\d])([A-Z])/g, '$1 $2')
    .replace(/^./, (c) => c.toUpperCase())
    .replace(/\bDem\b/g, 'DEM')
    .replace(/\bOrtho\b/g, 'Ortho')
    .replace(/\bPc\b/g, 'Point Cloud');

const formatSettingValue = (value: string | number | boolean): string => {
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (typeof value === 'string') {
    return value.replace(/_/g, ' ');
  }
  return String(value);
};

const formatDuration = (start: string, end: string): string => {
  const totalSeconds = Math.max(
    0,
    Math.round((new Date(end).getTime() - new Date(start).getTime()) / 1000)
  );
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }
  return `${seconds}s`;
};

export {
  checkForExistingJobs,
  checkImageProcessingJobProgress,
  fetchRawDataProcessingJobs,
  fetchUserExtensions,
  formatDuration,
  formatSettingKey,
  formatSettingValue,
  startImageProcessingJob,
};
