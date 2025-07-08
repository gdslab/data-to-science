import axios, { AxiosResponse, isAxiosError } from 'axios';

import {
  FetchPotGroupModuleParams,
  IndoorProjectDataVizAPIResponse,
} from '../IndoorProject.d';

export async function fetchPotGroupModuleVisualizationData({
  indoorProjectId,
  indoorProjectDataId,
  cameraOrientation,
  groupBy,
}: FetchPotGroupModuleParams): Promise<IndoorProjectDataVizAPIResponse> {
  let endpoint = `${import.meta.env.VITE_API_V1_STR}/indoor_projects/`;
  endpoint += `${indoorProjectId}/uploaded/${indoorProjectDataId}/data_for_viz`;

  try {
    const queryParams = {
      camera_orientation: cameraOrientation,
      group_by: groupBy,
    };
    const results: AxiosResponse<IndoorProjectDataVizAPIResponse> =
      await axios.get(endpoint, { params: queryParams });
    return results.data;
  } catch (error) {
    if (isAxiosError(error)) {
      // Axios-specific error handling
      const status = error.response?.status || 500;
      const message = error.response?.data?.message || error.message;

      throw {
        status,
        message: `Failed to generate chart data: ${message}`,
      };
    } else {
      // Generic error handling
      throw {
        status: 500,
        message: 'An unexpected error occurred.',
      };
    }
  }
}
