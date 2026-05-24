import { useContext } from 'react';
import { Link, Outlet } from 'react-router';

import AuthContext from '../../AuthContext';
import brandLogo from '../../assets/d2s-logo-white.svg';

export default function RootExplore() {
  const { user } = useContext(AuthContext);

  return (
    <div className="h-screen">
      <nav className="bg-primary h-16 flex items-center justify-between px-4 sm:px-6">
        <Link to={user ? '/home' : '/'}>
          <img className="h-8" src={brandLogo} alt="Data to Science" />
        </Link>
        <div className="flex items-center gap-4 text-sm font-semibold text-white">
          {user ? (
            <Link
              to="/home"
              className="hover:text-amber-300 transition-colors"
            >
              My workspace
            </Link>
          ) : (
            <>
              <Link
                to="/auth/login"
                className="hover:text-amber-300 transition-colors"
              >
                Sign in
              </Link>
              <Link
                to="/auth/register"
                className="rounded-md bg-amber-400 px-3 py-1.5 text-sm text-black hover:bg-amber-300 transition-colors"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </nav>
      <div className="h-[calc(100vh-64px)]">
        <Outlet />
      </div>
    </div>
  );
}
