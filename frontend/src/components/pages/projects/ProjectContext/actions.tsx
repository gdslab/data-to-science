import { IForester } from '../Project';
import { GeoJSONFeature, MapLayerFeatureCollection } from '../Project';
import { Flight } from '../Project';
import { Project } from '../ProjectList';
import { ProjectMember } from '../ProjectAccess';

export type IForesterAction = { type: string; payload: IForester[] | null };
export type LocationAction = { type: string; payload: GeoJSONFeature | null };
export type FlightsAction = { type: string; payload: Flight[] | null };
export type FlightsFilterSelectionAction = { type: string; payload?: string[] };
export type MapLayersAction = { type: string; payload?: MapLayerFeatureCollection[] };
export type ProjectAction = { type: string; payload: Project | null };
export type ProjectMembersAction = { type: string; payload: ProjectMember[] | null };
export type ProjectRoleAction = { type: string; payload: string | undefined };
