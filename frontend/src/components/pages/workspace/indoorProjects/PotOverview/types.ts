import {
  IndoorProjectDataSpreadsheetAPIResponse,
  IndoorProjectDataVizAPIResponse,
  IndoorProjectDataVizRecord,
} from '../IndoorProject';

export interface CircleItemProps {
  group: IndoorProjectDataVizRecord;
  treatment: string;
  hsvColor: {
    hue: number;
    saturation: number;
    intensity: number;
  };
  url: string;
}

export interface PotOverviewProps {
  data: IndoorProjectDataVizAPIResponse;
  indoorProjectDataSpreadsheet: IndoorProjectDataSpreadsheetAPIResponse;
  indoorProjectId: string;
}

export interface SliderMark {
  value: number;
  label: string;
}
