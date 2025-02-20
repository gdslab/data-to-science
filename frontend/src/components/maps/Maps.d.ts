import { FeatureCollection, Point } from 'geojson';

import { DataProduct, Flight } from '../pages/projects/Project';
import { Project } from '../pages/projects/ProjectList';

export type MapTool = 'map' | 'compare' | 'timeline';

export type ActiveDataProductAction = {
  type: string;
  payload: DataProduct | Partial<DataProduct> | null;
};

export type ActiveMapToolAction = { type: string; payload: MapTool };

export type ActiveProjectAction = { type: string; payload: Project | null };

export type BBox = [number, number, number, number];

export type FlightsAction = { type: string; payload: Flight[] };

export type ProjectsAction = { type: string; payload: Project[] | null };

export type ProjectsLoadedAction = { type: string; payload: boolean };

export type ProjectsVisibleAction = { type: string; payload: string[] };

export type GeoRasterIdAction = { type: string };

export type MapboxAccessTokenAction = { type: string; payload: string };

export type SymbologySettingsAction = {
  type: string;
  payload: SymbologySettings;
};

export type TileScaleAction = { type: string; payload: number };
