import { createBrowserRouter } from 'react-router-dom';

import ErrorPage from './components/ErrorPage';
import FlightForm from './components/forms/FlightForm';
import Landing from './components/Landing';
import LoginForm from './components/auth/LoginForm';
import Logout from './components/auth/Logout';
import Map from './components/map';
import ProjectDetail from './components/forms/ProjectDetail';
import ProjectForm from './components/forms/ProjectForm';
import ProjectList from './components/forms/ProjectList';
import RegistrationForm from './components/auth/RegistrationForm';
import Root from './components/layout/Root';
import Teams from './components/forms/Teams/Teams';
import TeamDetail from './components/forms/TeamDetail';
import TeamForm from './components/forms/TeamForm';

// data loaders
import { loader as projectDetailLoader } from './components/forms/ProjectDetail/ProjectDetail';
import { loader as projectFormLoader } from './components/forms/ProjectForm/ProjectForm';
import { loader as projectListLoader } from './components/forms/ProjectList/ProjectList';
import { loader as teamDetailLoader } from './components/forms/TeamDetail/TeamDetail';
import { loader as teamsLoader } from './components/forms/Teams/Teams';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Root />,
    errorElement: <ErrorPage />,
    children: [
      {
        path: '/',
        element: <Landing />,
      },
      {
        path: '/auth/register',
        element: <RegistrationForm />,
      },
      {
        path: '/auth/login',
        element: <LoginForm />,
      },
      {
        path: '/auth/logout',
        element: <Logout />,
      },
      {
        path: '/home',
        element: <Map />,
      },
      {
        path: '/teams',
        element: <Teams />,
        loader: teamsLoader,
        children: [
          {
            path: '/teams/:teamId',
            element: <TeamDetail />,
            loader: teamDetailLoader,
          },
          {
            path: '/teams/create',
            element: <TeamForm />,
          },
        ],
      },
      {
        path: '/projects',
        element: <ProjectList />,
        loader: projectListLoader,
      },
      {
        path: '/projects/create',
        element: <ProjectForm />,
        loader: projectFormLoader,
      },
      {
        path: '/projects/:projectId',
        element: <ProjectDetail />,
        loader: projectDetailLoader,
      },
      {
        path: '/projects/:projectId/datasets/:datasetId',
        element: <FlightForm />,
      },
    ],
  },
]);
