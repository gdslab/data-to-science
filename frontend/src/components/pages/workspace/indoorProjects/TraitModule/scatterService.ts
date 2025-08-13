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
  plottedBy,
  accordingTo,
  targetTraitX,
  targetTraitY,
  potBarcode,
}: FetchTraitScatterModuleParams): Promise<IndoorProjectDataVizScatterAPIResponse> {
  let endpoint = `/indoor_projects/${indoorProjectId}/uploaded/${indoorProjectDataId}/data_for_scatter`;

  try {
    const queryParams: Record<string, any> = {
      camera_orientation: cameraOrientation,
      plotted_by: plottedBy,
      according_to: accordingTo,
      trait_x: targetTraitX,
      trait_y: targetTraitY,
    };

    // Add pot_barcode to query params if provided
    if (potBarcode !== undefined) {
      queryParams.pot_barcode = potBarcode;
    }
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
