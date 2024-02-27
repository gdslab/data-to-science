import { Flight } from '../Project';
import { Project } from '../ProjectList';
import { ProjectMember } from '../ProjectAccess';

export type FlightsAction = { type: string; payload: Flight[] | null };
export type ProjectAction = { type: string; payload: Project | null };
export type ProjectMembersAction = { type: string; payload: ProjectMember[] | null };
export type ProjectRoleAction = { type: string; payload: string | undefined };
