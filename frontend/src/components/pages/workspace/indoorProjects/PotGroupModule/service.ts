import { AxiosResponse, isAxiosError } from 'axios';

import api from '../../../../../api';
import {
  FetchPotGroupModuleParams,
  IndoorProjectDataVizAPIResponse,
} from '../IndoorProject.d';

export async function fetchPotGroupModuleVisualizationData({
  indoorProjectId,
  indoorProjectDataId,
  cameraOrientation,
  plottedBy,
  accordingTo,
  potBarcode,
}: FetchPotGroupModuleParams): Promise<IndoorProjectDataVizAPIResponse> {
  const endpoint = `/indoor_projects/${indoorProjectId}/uploaded/${indoorProjectDataId}/data_for_viz`;

  try {
    const queryParams = {
      camera_orientation: cameraOrientation,
      plotted_by: plottedBy,
      according_to: accordingTo,
      ...(potBarcode !== undefined ? { pot_barcode: potBarcode } : {}),
    };
    const results: AxiosResponse<IndoorProjectDataVizAPIResponse> =
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
