import { AxiosResponse } from 'axios';
import { useEffect } from 'react';
import { Params, useLoaderData } from 'react-router-dom';

import { User } from '../../../../AuthContext';
import { useProjectContext } from './ProjectContext';
import { Flight, Project, ProjectLoaderData } from './Project';
import { ProjectMember } from './ProjectAccess';
import ProjectDetailEditForm from './ProjectDetailEditForm';
import ProjectTabNav from './ProjectTabNav';
import { Team } from '../../teams/Teams';
import { getProjectMembers } from './ProjectContext/ProjectContext';

import api from '../../../../api';

export async function loader({ params }: { params: Params<string> }) {
  const profile = localStorage.getItem('userProfile');
  const user: User | null = profile ? JSON.parse(profile) : null;
  if (!user) return null;

  try {
    const project: AxiosResponse<Project> = await api.get(
      `/projects/${params.projectId}`
    );
    const project_member: AxiosResponse<ProjectMember> = await api.get(
      `/projects/${params.projectId}/members/${user.id}`
    );
    const flights: AxiosResponse<Flight[]> = await api.get(
      `/projects/${params.projectId}/flights`
    );
    const teams: AxiosResponse<Team[]> = await api.get('/teams', {
      params: { owner_only: true },
    });

    if (project && project_member && flights && teams) {
      const teamsf = teams.data;
      teamsf.unshift({
        title: 'No team',
        id: '',
        is_owner: false,
        description: '',
        exts: [],
      });
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
  const { project, role, flights, teams } =
    useLoaderData() as ProjectLoaderData;

  const {
    projectRole,
    flights: flightsPrev,
    flightsDispatch,
    flightsFilterSelection,
    flightsFilterSelectionDispatch,
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
    if (project) getProjectMembers(project.id, projectMembersDispatch);
  }, [project.team_id]);

  useEffect(() => {
    if (flights) flightsDispatch({ type: 'set', payload: flights });
    // check filter option for new flight if it is the first flight with its sensor
    if (flights && flightsPrev) {
      // no previous flights, so select any sensor in flights
      if (flightsPrev.length === 0) {
        flightsFilterSelectionDispatch({
          type: 'set',
          payload: [...new Set(flights.map(({ sensor }) => sensor))],
        });
      } else {
        // compare previous sensors with sensor in new flights
        const prevSensors = flightsPrev.map(({ sensor }) => sensor);
        const newSensors = flights
          .filter(
            ({ sensor }) =>
              prevSensors.indexOf(sensor) < 0 &&
              flightsFilterSelection.indexOf(sensor) < 0
          )
          .map(({ sensor }) => sensor);
        // if any new sensors were found, add to filter selection options and check
        if (newSensors.length > 0) {
          flightsFilterSelectionDispatch({
            type: 'set',
            payload: [...flightsFilterSelection, ...newSensors],
          });
        }
      }
    }
  }, [flights]);

  if (project) {
    return (
      <div className="flex flex-col h-full gap-4 p-4">
        {projectRole === 'owner' || projectRole === 'manager' ? (
          <ProjectDetailEditForm project={project} teams={teams} />
        ) : (
          <div>
            <span className="block text-lg font-bold mb-0">
              {project.title}
            </span>
            <span className="block my-1 mx-0 text-gray-600 text-wrap break-all">
              {project.description}
            </span>
          </div>
        )}
        <div className="grow min-h-0">
          <ProjectTabNav />
        </div>
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
