import {
  IndoorProjectDataVizAPIResponse,
  NumericColumns,
  IndoorProjectDataPlantAPIResponse,
} from '../IndoorProject';

export interface PlantDetailAndChart extends IndoorProjectDataPlantAPIResponse {
  topChart: IndoorProjectDataVizAPIResponse;
  sideChart: IndoorProjectDataVizAPIResponse;
  numericColumns: NumericColumns;
}
