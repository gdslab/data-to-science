import { AxiosResponse, isAxiosError } from 'axios';

import api from '../../../../../api';
import {
  FetchTraitModuleParams,
  IndoorProjectDataViz2APIResponse,
} from '../IndoorProject';

export async function fetchTraitModuleVisualizationData({
  indoorProjectId,
  indoorProjectDataId,
  cameraOrientation,
  groupBy,
  targetTrait,
}: FetchTraitModuleParams): Promise<IndoorProjectDataViz2APIResponse> {
  let endpoint = `/indoor_projects/${indoorProjectId}/uploaded/${indoorProjectDataId}/data_for_viz2`;

  try {
    const queryParams = {
      camera_orientation: cameraOrientation,
      group_by: groupBy,
      trait: targetTrait,
    };
    const results: AxiosResponse<IndoorProjectDataViz2APIResponse> =
      await api.get(endpoint, { params: queryParams });
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
