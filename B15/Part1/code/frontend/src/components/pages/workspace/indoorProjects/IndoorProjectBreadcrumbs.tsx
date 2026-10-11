import { useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router';

import { classNames } from '../../../utils';
import { useIndoorProjectContext } from './IndoorProjectContext';

export default function IndoorProjectBreadcrumbs() {
  const {
    state: { indoorProject },
  } = useIndoorProjectContext();
  const location = useLocation();
  const { indoorProjectId, indoorProjectDataId, indoorProjectPlantId } =
    useParams();
  const [indoorProjectCrumb, setIndoorProjectCrumb] = useState('');
  const [plantCrumb, setPlantCrumb] = useState('');

  const slug = location.pathname.split('/').slice(-1)[0];

  useEffect(() => {
    if (indoorProjectId) {
      if (indoorProject) {
        setIndoorProjectCrumb(indoorProject.title);
        localStorage.setItem(
          `indoor_project_${indoorProject.id}`,
          indoorProject.title
        );
      } else {
        const storedIndoorProjectCrumb = localStorage.getItem(
          `indoor_project_${indoorProjectId}`
        );
        if (storedIndoorProjectCrumb)
          setIndoorProjectCrumb(storedIndoorProjectCrumb);
      }
    } else {
      setIndoorProjectCrumb('');
    }
  }, [indoorProject, indoorProjectId]);

  useEffect(() => {
    if (indoorProjectPlantId) {
      // For plant detail pages, we can show the plant ID in breadcrumbs
      const plantDisplayName = `Plant ${indoorProjectPlantId}`;
      setPlantCrumb(plantDisplayName);
      localStorage.setItem(
        `indoor_project_plant_${indoorProjectPlantId}`,
        plantDisplayName
      );
    } else {
      setPlantCrumb('');
    }
  }, [indoorProjectPlantId]);

  if (indoorProjectId) {
    return (
      <nav aria-label="Breadcrumb">
        <ol className="flex items-center gap-1 text-sm text-gray-600">
          <li>
            <Link
              to="/indoor_projects"
              className="block transition hover:text-gray-700"
            >
              <span className="ms-1.5 text-xs font-medium">
                {' '}
                Indoor Projects{' '}
              </span>
            </Link>
          </li>

          {indoorProjectCrumb ? (
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
                  to={`/indoor_projects/${indoorProjectId}`}
                  className={classNames(
                    !plantCrumb && !['access'].includes(slug)
                      ? 'font-semibold'
                      : '',
                    'block transition hover:text-gray-700 max-w-60 truncate'
                  )}
                >
                  {indoorProjectCrumb}
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
                  to={`/indoor_projects/${indoorProjectId}/access`}
                  className="block transition font-semibold hover:text-gray-700"
                >
                  Manage Access
                </Link>
              </li>
            </>
          ) : null}

          {indoorProjectCrumb && plantCrumb ? (
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
                  to={`/indoor_projects/${indoorProjectId}/uploaded/${indoorProjectDataId}/plants/${indoorProjectPlantId}`}
                  className="block transition font-semibold hover:text-gray-700"
                >
                  {plantCrumb}
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
