import { Outlet } from 'react-router-dom';

import ProjectBreadcrumbs from './Breadcrumbs';
import { ProjectContextProvider } from './ProjectContext';

export default function ProjectLayout() {
  return (
    <ProjectContextProvider>
      <div className="h-full flex flex-col">
        <div className="p-4">
          <ProjectBreadcrumbs />
        </div>
        <div className="grow min-h-0">
          <Outlet />
        </div>
      </div>
    </ProjectContextProvider>
  );
}
