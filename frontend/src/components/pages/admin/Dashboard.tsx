import { Outlet } from 'react-router-dom';

import SidePanel from './SidePanel';

export default function Dashboard() {
  return (
    <div className="flex flex-row h-full">
      <SidePanel />
      <Outlet />
    </div>
  );
}
