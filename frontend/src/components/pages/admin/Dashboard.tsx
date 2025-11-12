import { Outlet } from 'react-router-dom';

import SidePanel from './SidePanel';

export default function Dashboard() {
  return (
    <div className="flex flex-row h-full w-full bg-white overflow-hidden">
      <div className="flex-shrink-0">
        <SidePanel />
      </div>
      <div className="flex-1 overflow-x-auto overflow-y-scroll">
        <Outlet />
      </div>
    </div>
  );
}
