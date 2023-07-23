import { useEffect, useState } from "react";
import { Link, Outlet } from "react-router-dom";

export default function Root() {
  const [hasJWT, toggleHasJWT] = useState(false);
  useEffect(() => {
    const accessToken = localStorage.getItem("access_token");
    if (accessToken) {
      toggleHasJWT(true);
    }
  }, []);
  return (
    <div className="wrapper">
      <div className="header">
        <nav>
          {hasJWT ? (
            <Link to="logout">Logout</Link>
          ) : (
            <>
              <Link to="/register">Register</Link> <Link to="/login">Login</Link>
            </>
          )}
        </nav>
      </div>
      <div className="sidebar">
        <nav>
          {hasJWT ? (
            <ul>
              <li>
                <Link to="/">Home</Link>
              </li>
              <li>
                <Link to="/teams">Teams</Link>
              </li>
              <li>
                <Link to="/projects">Projects</Link>
              </li>
            </ul>
          ) : null}
        </nav>
      </div>
      <div className="content">
        <Outlet />
      </div>
      <div className="footer"></div>
    </div>
  );
}
