import { AxiosResponse, isAxiosError } from 'axios';

import api from '../../../../../api';
import {
  FetchTraitScatterModuleParams,
  IndoorProjectDataVizScatterAPIResponse,
} from '../IndoorProject';

export async function fetchTraitScatterModuleVisualizationData({
  indoorProjectId,
  indoorProjectDataId,
  cameraOrientation,
  groupBy,
  targetTraitX,
  targetTraitY,
}: FetchTraitScatterModuleParams): Promise<IndoorProjectDataVizScatterAPIResponse> {
  let endpoint = `${import.meta.env.VITE_API_V1_STR}/indoor_projects/`;
  endpoint += `${indoorProjectId}/uploaded/${indoorProjectDataId}/data_for_scatter`;

  try {
    const queryParams = {
      camera_orientation: cameraOrientation,
      group_by: groupBy,
      trait_x: targetTraitX,
      trait_y: targetTraitY,
    };
    const results: AxiosResponse<IndoorProjectDataVizScatterAPIResponse> =
      await api.get(endpoint, { params: queryParams });
    return results.data;
  } catch (error) {
    if (isAxiosError(error)) {
      // Axios-specific error handling
      const status = error.response?.status || 500;
      const message = error.response?.data?.message || error.message;

      throw {
        status,
        message: `Failed to generate scatter plot data: ${message}`,
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
