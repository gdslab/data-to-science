import { Outlet } from 'react-router';

import IndoorProjectBreadcrumbs from './IndoorProjectBreadcrumbs';
import { IndoorProjectProvider } from './IndoorProjectContext';

export default function IndoorProjectLayout() {
  return (
    <IndoorProjectProvider>
      <div className="h-full flex flex-col">
        <div className="p-4">
          <IndoorProjectBreadcrumbs />
        </div>
        <div className="grow min-h-0">
          <Outlet />
        </div>
      </div>
    </IndoorProjectProvider>
  );
}
