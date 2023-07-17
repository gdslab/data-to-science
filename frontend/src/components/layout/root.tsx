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
        <nav>{hasJWT ? <span>Logged in</span> : <span>Logged out</span>}</nav>
      </div>
      <div className="sidebar">
        <nav>
          <ul>
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/register">Register</Link>
            </li>
            <li>
              <Link to="/login">Login</Link>
            </li>
            <li>
              <Link to="/projects">Project</Link>
            </li>
            <li>
              <Link to="/flights">Flight</Link>
            </li>
          </ul>
        </nav>
      </div>
      <div className="content">
        <Outlet />
      </div>
      <div className="footer"></div>
    </div>
  );
}
