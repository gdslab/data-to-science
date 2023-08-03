import { Outlet } from 'react-router-dom';

import Navbar from './Navbar';

export default function Root() {
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
