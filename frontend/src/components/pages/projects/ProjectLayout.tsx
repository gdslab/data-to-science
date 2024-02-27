import { Outlet } from 'react-router-dom';

import ProjectBreadcrumbs from './Breadcrumbs';
import ProjectContextProvider from './ProjectContext';
import FlightContextProvider from './FlightContext';

export default function ProjectLayout() {
  return (
    <ProjectContextProvider>
      <FlightContextProvider>
        <div className="h-full flex flex-col">
          <div className="p-4">
            <ProjectBreadcrumbs />
          </div>
          <div className="grow min-h-0">
            <Outlet />
          </div>
        </div>
      </FlightContextProvider>
    </ProjectContextProvider>
  );
}
