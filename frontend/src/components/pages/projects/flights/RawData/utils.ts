import { AxiosResponse, isAxiosError } from 'axios';

import { Job } from '../../Project';

import { ImageProcessingSettings } from './RawData.types';

import api from '../../../../../api';

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

const fetchUserExtensions = async (): Promise<boolean> => {
  try {
    const response: AxiosResponse<string[]> = await api.get(
      '/users/extensions'
    );
    if (response.status === 200) {
      return response.data.indexOf('image_processing') > -1;
    } else {
      console.log('Unable to fetch user');
      return false;
    }
  } catch (err) {
    if (isAxiosError(err) && err.response && err.response.data.detail) {
      throw new Error(err.response.data.detail);
    } else {
      throw new Error('Unable to fetch user');
    }
  }
};

const startImageProcessingJob = async (
  flightId: string,
  projectId: string,
  rawDataId: string,
  settings: ImageProcessingSettings
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
    if (isAxiosError(err) && err.response && err.response.data.detail) {
      throw new Error(err.response.data.detail);
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
