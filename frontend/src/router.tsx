import { createBrowserRouter } from 'react-router-dom';

// pages and data loaders
import ErrorPage from './components/ErrorPage';
import FlightForm from './components/forms/FlightForm';
import Landing from './components/Landing';
import LoginForm from './components/auth/LoginForm';
import Logout from './components/auth/Logout';
import Map from './components/map';
import Profile from './components/auth/Profile';
import ProjectDetail, {
  loader as projectDetailLoader,
} from './components/forms/ProjectDetail';
import ProjectForm, {
  loader as projectFormLoader,
} from './components/forms/ProjectForm';
import ProjectList, {
  loader as projectListLoader,
} from './components/forms/ProjectList';
import RegistrationForm from './components/auth/RegistrationForm';
import Teams, { loader as teamsLoader } from './components/forms/Teams';
import TeamDetail, { loader as teamDetailLoader } from './components/forms/TeamDetail';
import TeamForm from './components/forms/TeamForm';

import { RootPublic, RootProtected } from './components/layout/Root';
import { RequireAuth } from './AuthContext';

export const router = createBrowserRouter([
  {
    // public pages
    element: <RootPublic />,
    errorElement: <ErrorPage />,
    children: [
      {
        path: '/',
        element: <Landing />,
      },
      {
        path: '/auth/login',
        element: <LoginForm />,
      },
      {
        path: '/auth/register',
        element: <RegistrationForm />,
      },
      {
        path: '/auth/logout',
        element: <Logout />,
      },
    ],
  },
  {
    // protected pages (require authentication)
    element: (
      <RequireAuth>
        <RootProtected />
      </RequireAuth>
    ),
    errorElement: <ErrorPage />,
    children: [
      {
        path: '/home',
        element: <Map />,
      },
      {
        path: '/auth/profile',
        element: <Profile />,
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
