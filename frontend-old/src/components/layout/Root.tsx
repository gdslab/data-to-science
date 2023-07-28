import { useContext } from "react";
import { Link, Outlet } from "react-router-dom";

import AuthContext from "../../AuthContext";

export default function Root() {
  const { user } = useContext(AuthContext);
  return (
    <div className="wrapper">
      <div className="header">
        <nav>
          {user ? (
            <Link to="/logout">Logout</Link>
          ) : (
            <>
              <Link to="/register">Register</Link> <Link to="/login">Login</Link>
            </>
          )}
        </nav>
      </div>
      <div className="content">
        <Outlet />
      </div>
      <div className="footer"></div>
    </div>
  );
}
