import { DataProduct, Flight } from '../pages/workspace/projects/Project';
import { Project } from '../pages/workspace/ProjectList';

export interface DSMSymbologySettings {
  colorRamp: string;
  max: number;
  meanStdDev: number;
  min: number;
  mode: string;
  userMin: number;
  userMax: number;
  opacity: number;
}

export interface OrthoSymbologySettings {
  mode: string;
  meanStdDev: number;
  red: {
    idx: number;
    min: number;
    max: number;
    userMin: number;
    userMax: number;
  };
  green: {
    idx: number;
    min: number;
    max: number;
    userMin: number;
    userMax: number;
  };
  blue: {
    idx: number;
    min: number;
    max: number;
    userMin: number;
    userMax: number;
  };
  opacity: number;
}

export type MapTool = 'map' | 'compare' | 'timeline';

export type SymbologySettings = DSMSymbologySettings | OrthoSymbologySettings;

export type ActiveDataProductAction = {
  type: string;
  payload: DataProduct | Partial<DataProduct> | null;
};

export type ActiveMapToolAction = { type: string; payload: MapTool };

export type ActiveProjectAction = { type: string; payload: Project | null };

export type FlightsAction = { type: string; payload: Flight[] };

export type ProjectsAction = { type: string; payload: Project[] | null };

export type ProjectsVisibleAction = { type: string; payload: string[] };

export type GeoRasterIdAction = { type: string };

export type MapboxAccessTokenAction = { type: string; payload: string };

export type SymbologySettingsAction = { type: string; payload: SymbologySettings };

export type TileScaleAction = { type: string; payload: number };
