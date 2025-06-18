import { IForester } from '../Project';
import { GeoJSONFeature, MapLayer } from '../Project';
import { Flight, ProjectModule, Project } from '../Project';
import { ProjectMember } from '../ProjectAccess';

export type IForesterAction = { type: string; payload: IForester[] | null };
export type LocationAction = { type: string; payload: GeoJSONFeature | null };
export type FlightsAction = { type: string; payload: Flight[] | null };
export type FlightsFilterSelectionAction = { type: string; payload?: string[] };
export type MapLayersAction = { type: string; payload?: MapLayer[] };
export type ProjectAction = { type: string; payload: Project | null };
export type ProjectFilterSelectionAction = { type: string; payload?: string[] };
export type ProjectMembersAction = {
  type: string;
  payload: ProjectMember[] | null;
};
export type ProjectModulesAction = {
  type: string;
  payload: ProjectModule[] | null;
};
export type ProjectRoleAction = { type: string; payload: string | undefined };
