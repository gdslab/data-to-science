import { ReactNode, useContext } from 'react';
import { Link } from 'react-router-dom';

import AuthContext from '../../AuthContext';

function NavLink({ path, children }: { path: string; children: ReactNode }) {
  return (
    <Link className="float-right font-bold mr-4 text-white" to={path}>
      {children}
    </Link>
  );
}

export default function Header() {
  const { user } = useContext(AuthContext);
  return (
    <nav className="h-10 leading-10 bg-indigo-500">
      {!user ? (
        <>
          <NavLink path="/auth/login">Login</NavLink>
          <NavLink path="/auth/register">Register</NavLink>
        </>
      ) : (
        <NavLink path="/auth/logout">Logout</NavLink>
      )}
    </nav>
  );
}
