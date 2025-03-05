import { useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';

import { classNames } from '../../../utils';
import { useProjectContext } from './ProjectContext';

export default function ProjectBreadcrumbs() {
  const { project, flights } = useProjectContext();
  const location = useLocation();
  const { flightId, projectId } = useParams();
  const [flightCrumb, setFlightCrumb] = useState('');
  const [projectCrumb, setProjectCrumb] = useState('');

  const slug = location.pathname.split('/').slice(-1)[0];

  useEffect(() => {
    if (projectId) {
      if (project) {
        setProjectCrumb(project.title);
        localStorage.setItem(project.id, project.title);
      } else {
        const storedProjectCrumb = localStorage.getItem(projectId);
        if (storedProjectCrumb) setProjectCrumb(storedProjectCrumb);
      }
    } else {
      setProjectCrumb('');
    }
  }, [project, projectId]);

  useEffect(() => {
    if (flightId) {
      if (flights && flights.length > 0) {
        const currentFlight = flights.filter(({ id }) => id === flightId);
        if (currentFlight && currentFlight.length > 0) {
          const sensorPlatformDate = `${currentFlight[0].name ? currentFlight[0].name + ' | ' : ''}${currentFlight[0].sensor} | ${currentFlight[0].platform} | ${currentFlight[0].acquisition_date}`;
          setFlightCrumb(sensorPlatformDate);
          localStorage.setItem(currentFlight[0].id, sensorPlatformDate);
        }
      } else {
        const storedFlightCrumb = localStorage.getItem(flightId);
        if (storedFlightCrumb) setFlightCrumb(storedFlightCrumb);
      }
    } else {
      setFlightCrumb('');
    }
  }, [flights, flightId]);

  if (projectId) {
    return (
      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-1 text-sm text-gray-600">
          <li>
            <Link to="/projects" className="block transition hover:text-gray-700">
              <span className="ms-1.5 text-xs font-medium"> Projects </span>
            </Link>
          </li>

          {projectCrumb ? (
            <>
              <li>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </li>
              <li>
                <Link
                  to={`/projects/${projectId}`}
                  className={classNames(
                    !flightCrumb && slug !== 'access' ? 'font-semibold' : '',
                    'block transition hover:text-gray-700 max-w-60 truncate'
                  )}
                >
                  {projectCrumb}
                </Link>
              </li>
            </>
          ) : null}

          {slug === 'access' ? (
            <>
              <li>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </li>

              <li>
                <Link
                  to={`/projects/${projectId}/access`}
                  className="block transition font-semibold hover:text-gray-700"
                >
                  Manage Access
                </Link>
              </li>
            </>
          ) : null}

          {projectCrumb && flightCrumb ? (
            <>
              <li>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </li>

              <li>
                <Link
                  to={`/projects/${projectId}/flights/${flightId}/data`}
                  className="block transition font-semibold hover:text-gray-700"
                >
                  {flightCrumb.split('_').join(' ')}
                </Link>
              </li>
            </>
          ) : null}
        </ol>
      </nav>
    );
  } else {
    return null;
  }
}
