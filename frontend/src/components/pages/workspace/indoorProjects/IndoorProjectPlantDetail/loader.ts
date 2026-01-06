import { AxiosResponse, isAxiosError } from 'axios';
import { Params } from 'react-router';

import api from '../../../../../api';
import {
  IndoorProjectDataPlantAPIResponse,
  IndoorProjectDataSpreadsheetAPIResponse,
  IndoorProjectDataVizAPIResponse,
  NumericColumns,
} from '../IndoorProject';
import { PlantDetailAndChart } from './types';

export function loader({ params }: { params: Params<string> }) {
  async function fetchPlantData(): Promise<PlantDetailAndChart> {
    try {
      const id = params.indoorProjectId;
      const dId = params.indoorProjectDataId;
      const pId = params.indoorProjectPlantId;

      const baseUrl = `/indoor_projects/${id}/uploaded`;

      const plantDetailEndpoint = `${baseUrl}/${dId}/plants/${pId}`;
      const plantChartEndpoint = `${baseUrl}/${dId}/data_for_viz`;

      const plantChartTopQueryParams = {
        camera_orientation: 'top',
        plotted_by: 'pots',
        according_to: 'single_pot',
        pot_barcode: pId,
      };
      const plantChartSideQueryParams = {
        camera_orientation: 'side',
        plotted_by: 'pots',
        according_to: 'single_pot',
        pot_barcode: pId,
      };

      const spreadsheetEndpoint = `${baseUrl}/${dId}`;

      const [
        detailResponse,
        chartTopResponse,
        chartSideResponse,
        spreadsheetResponse,
      ]: [
        AxiosResponse<IndoorProjectDataPlantAPIResponse>,
        AxiosResponse<IndoorProjectDataVizAPIResponse>,
        AxiosResponse<IndoorProjectDataVizAPIResponse>,
        AxiosResponse<IndoorProjectDataSpreadsheetAPIResponse>
      ] = await Promise.all([
        api.get(plantDetailEndpoint),
        api.get(plantChartEndpoint, { params: plantChartTopQueryParams }),
        api.get(plantChartEndpoint, { params: plantChartSideQueryParams }),
        api.get(spreadsheetEndpoint),
      ]);

      const detailData = detailResponse.data;
      const chartTopData = chartTopResponse.data;
      const chartSideData = chartSideResponse.data;
      const numericColumns: NumericColumns =
        spreadsheetResponse.data.numeric_columns;

      return {
        ...detailData,
        topChart: chartTopData,
        sideChart: chartSideData,
        numericColumns,
      };
    } catch (error) {
      if (isAxiosError(error)) {
        const status = error.response?.status || 500;
        const message = error.response?.data?.message || error.message;
        throw {
          status,
          message: `Failed to fetch plant data: ${message}`,
        };
      } else {
        throw {
          status: 500,
          message: 'An unexpected error occurred.',
        };
      }
    }
  }

  return { plantData: fetchPlantData() };
}
