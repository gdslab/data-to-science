import { createBrowserRouter } from 'react-router-dom';

// pages and data loaders
import DataProducts, {
  loader as dataProductsLoader,
} from './components/pages/projects/flights/dataProducts/DataProducts';
import ErrorPage from './components/ErrorPage';
import FlightData, {
  loader as flightDataLoader,
} from './components/pages/projects/flights/FlightData';
import FlightForm, {
  loader as flightFormLoader,
} from './components/pages/projects/flights/FlightForm';
import Landing from './components/Landing';
import LoginForm from './components/pages/auth/LoginForm';
import Logout from './components/pages/auth/Logout';
import Map, { loader as mapLoader } from './components/maps/Map';
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
import RawData, {
  loader as rawDataLoader,
} from './components/pages/projects/flights/rawData/RawData';
import RegistrationForm from './components/pages/auth/RegistrationForm';
import Teams, { loader as teamsLoader } from './components/pages/teams/Teams';
import TeamCreate from './components/pages/teams/TeamCreate';
import TeamDetail, {
  loader as teamDetailLoader,
} from './components/pages/teams/TeamDetail';

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
        loader: mapLoader,
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
        element: <FlightData />,
        loader: flightDataLoader,
        children: [
          {
            path: '/projects/:projectId/flights/:flightId/raw',
            element: <RawData />,
            loader: rawDataLoader,
          },
          {
            path: '/projects/:projectId/flights/:flightId/products',
            element: <DataProducts />,
            loader: dataProductsLoader,
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
