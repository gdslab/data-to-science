import { Outlet } from 'react-router-dom';

import ProjectBreadcrumbs from './Breadcrumbs';
import ProjectContextProvider from './ProjectContext';
import FieldCampaignContextProvider from './fieldCampaigns/FieldCampaignContext';
import FlightContextProvider from './FlightContext';

export default function ProjectLayout() {
  return (
    <ProjectContextProvider>
      <FlightContextProvider>
        <FieldCampaignContextProvider>
          <div className="h-full flex flex-col">
            <div className="p-4">
              <ProjectBreadcrumbs />
            </div>
            <div className="grow min-h-0">
              <Outlet />
            </div>
          </div>
        </FieldCampaignContextProvider>
      </FlightContextProvider>
    </ProjectContextProvider>
  );
}
