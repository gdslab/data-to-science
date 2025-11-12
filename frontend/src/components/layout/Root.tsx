import { Outlet } from 'react-router-dom';

import Navbar from './Navbar';

export function RootPublic() {
  return (
    <div className="h-screen">
      <div className="h-full">
        <Outlet />
      </div>
    </div>
  );
}

export function RootProtected() {
  return (
    <div className="h-screen">
      <div>
        <Navbar />
      </div>
      {/* subtract navbar from div height */}
      <div className="h-[calc(100vh-64px)]">
        <Outlet />
      </div>
    </div>
  );
}
