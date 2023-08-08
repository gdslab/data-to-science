import { Outlet } from 'react-router-dom';

import Navbar from './Navbar';

export function RootNonUser() {
  return (
    <div className="h-screen">
      <div className="h-full">
        <Outlet />
      </div>
    </div>
  );
}

export function RootUser() {
  return (
    <div className="h-screen">
      <div>
        <Navbar />
      </div>
      <div className="h-[calc(100%_-_64px)]">
        <Outlet />
      </div>
    </div>
  );
}
