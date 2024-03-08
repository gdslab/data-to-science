import axios, { AxiosResponse } from 'axios';
import { useEffect } from 'react';
import { Params, useLoaderData, useParams } from 'react-router-dom';

import { User } from '../../../AuthContext';
import { useProjectContext } from './ProjectContext';

import { Flight, Project, ProjectLoaderData } from './Project';
import { ProjectMember } from './ProjectAccess';
import ProjectDetailEditForm from './ProjectDetailEditForm';
import { Team } from '../teams/Teams';
import ProjectFlights from './ProjectFlights';
import { getProjectMembers } from './ProjectContext/ProjectContext';

export async function loader({ params }: { params: Params<string> }) {
  const profile = localStorage.getItem('userProfile');
  const user: User | null = profile ? JSON.parse(profile) : null;
  if (!user) return null;

  try {
    const project: AxiosResponse<Project> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}`
    );
    const project_member: AxiosResponse<ProjectMember> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/members/${
        user.id
      }`
    );
    const flights: AxiosResponse<Flight[]> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/flights`
    );
    const teams: AxiosResponse<Team[]> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/teams`
    );

    if (project && project_member && flights && teams) {
      const teamsf = teams.data;
      teamsf.unshift({ title: 'No team', id: '', is_owner: false, description: '' });
      return {
        project: project.data,
        role: project_member.data.role,
        flights: flights.data,
        teams: teamsf,
      };
    } else {
      return {
        project: null,
        role: null,
        flights: [],
        teams: [],
      };
    }
  } catch (err) {
    return {
      project: null,
      role: null,
      flights: [],
      teams: [],
    };
  }
}

export default function ProjectDetail() {
  const { project, role, flights, teams } = useLoaderData() as ProjectLoaderData;

  const params = useParams();
  const {
    projectRole,
    flightsDispatch,
    projectDispatch,
    projectMembersDispatch,
    projectRoleDispatch,
  } = useProjectContext();

  useEffect(() => {
    if (role) projectRoleDispatch({ type: 'set', payload: role });
  }, [role]);

  useEffect(() => {
    // @ts-ignore
    if (project) projectDispatch({ type: 'set', payload: project });
  }, [project]);

  useEffect(() => {
    // update project members if team changes
    if (project) getProjectMembers(params, projectMembersDispatch);
  }, [project.team_id]);

  useEffect(() => {
    if (flights) flightsDispatch({ type: 'set', payload: flights });
  }, [flights]);

  if (project) {
    return (
      <div className="flex flex-col h-full gap-4 p-4">
        {projectRole === 'owner' || projectRole === 'manager' ? (
          <ProjectDetailEditForm project={project} teams={teams} />
        ) : (
          <div>
            <h2 className="mb-0">{project.title}</h2>
            <span className="text-gray-600">{project.description}</span>
          </div>
        )}
        <ProjectFlights />
      </div>
    );
  } else {
    return (
      <div className="flex flex-col h-full gap-4 p-4">
        Unable to load selected project
      </div>
    );
  }
}
