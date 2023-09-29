import { createBrowserRouter } from 'react-router-dom';

// pages and data loaders
import ErrorPage from './components/ErrorPage';
import FlightData, {
  loader as flightDataLoader,
} from './components/pages/projects/flights/FlightData';
import FlightDetail, {
  loader as flightDetailLoader,
} from './components/pages/projects/flights/FlightDetail';
import FlightForm, {
  loader as flightFormLoader,
} from './components/pages/projects/flights/FlightForm';
import Landing from './components/Landing';
import LoginForm from './components/pages/auth/LoginForm';
import Logout from './components/pages/auth/Logout';
import MapLayout, { loader as mapLayoutLoader } from './components/maps/MapLayout';
import Profile from './components/pages/auth/Profile';
import ProjectDetail, {
  loader as projectDetailLoader,
} from './components/pages/projects/ProjectDetail';
import ProjectForm, {
  loader as projectFormLoader,
} from './components/pages/projects/ProjectForm';
import ProjectList, {
  loader as projectListLoader,
} from './components/pages/projects/ProjectList';
import RegistrationForm from './components/pages/auth/RegistrationForm';
import Teams, { loader as teamsLoader } from './components/pages/teams/Teams';
import TeamCreate from './components/pages/teams/TeamCreate';
import TeamDetail, {
  loader as teamDetailLoader,
} from './components/pages/teams/TeamDetail';

import SymbologyControl from './components/maps/SymbologyControl';

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
      {
        path: '/test',
        element: <SymbologyControl />,
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
        element: <MapLayout />,
        loader: mapLayoutLoader,
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
            element: <TeamCreate />,
            loader: projectListLoader,
          },
        ],
      },
      {
        path: '/projects/:projectId/flights/create',
        element: <FlightForm />,
        loader: flightFormLoader,
      },
      {
        path: '/projects/:projectId/flights/:flightId',
        element: <FlightDetail />,
        loader: flightDetailLoader,
        children: [
          {
            path: '/projects/:projectId/flights/:flightId/data',
            element: <FlightData />,
            loader: flightDataLoader,
          },
        ],
      },
      {
        path: '/projects/:projectId',
        element: <ProjectDetail />,
        loader: projectDetailLoader,
      },
      {
        path: '/projects/create',
        element: <ProjectForm />,
        loader: projectFormLoader,
      },
      {
        path: '/projects',
        element: <ProjectList />,
        loader: projectListLoader,
      },
    ],
  },
]);
