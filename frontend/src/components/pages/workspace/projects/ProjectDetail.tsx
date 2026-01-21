import { useEffect } from 'react';
import { useOutletContext } from 'react-router';

import { useProjectContext } from './ProjectContext';
import ProjectDetailEditForm from './ProjectDetailEditForm';
import ProjectTabNav from './ProjectTabNav';
import { getProjectMembers } from './ProjectContext/ProjectContext';
import { ProjectLayoutData } from './ProjectLayout';

export default function ProjectDetail() {
  const layoutData = useOutletContext<ProjectLayoutData>();
  const { project, project_modules, teams } = layoutData;

  const { projectRole, projectMembersDispatch } = useProjectContext();

  const projectId = project?.id;
  const teamId = project?.team_id;

  useEffect(() => {
    // update project members if team changes
    if (!projectId || !teamId) return;

    getProjectMembers(projectId, projectMembersDispatch);
  }, [projectId, projectMembersDispatch, teamId]);

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
            {project.created_by && (
              <span className="block text-sm text-gray-500">
                Created by: {project.created_by.first_name}{' '}
                {project.created_by.last_name}
              </span>
            )}
            <span className="block my-1 mx-0 text-gray-600 text-wrap break-all">
              {project.description}
            </span>
          </div>
        )}
        <div className="grow min-h-0">
          <ProjectTabNav project_modules={project_modules} />
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
