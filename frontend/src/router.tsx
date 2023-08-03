import axios from 'axios';
import { createBrowserRouter } from 'react-router-dom';

import ErrorPage from './components/ErrorPage';
import FlightForm from './components/forms/FlightForm';
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

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Root />,
    errorElement: <ErrorPage />,
    children: [
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
        loader: async () => {
          const response = await axios.get('/api/v1/teams/');
          if (response) {
            return response.data;
          } else {
            return [];
          }
        },
        children: [
          {
            path: '/teams/:teamId',
            element: <TeamDetail />,
            loader: async ({ params }) => {
              const response = await axios.get(`/api/v1/teams/${params.teamId}`);
              if (response) {
                return response.data;
              } else {
                return null;
              }
            },
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
        loader: async () => {
          const response = await axios.get('/api/v1/projects/', {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            },
          });
          if (response) {
            return response.data;
          } else {
            return [];
          }
        },
      },
      {
        path: '/projects/create',
        element: <ProjectForm />,
        loader: async () => {
          const response = await axios.get('/api/v1/teams/', {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            },
          });
          if (response) {
            const teams = response.data;
            teams.unshift({ title: 'No team', id: '' });
            return teams;
          } else {
            return [];
          }
        },
      },
      {
        path: '/projects/:projectId',
        element: <ProjectDetail />,
        loader: async ({ params }) => {
          const response = await axios.get(`/api/v1/projects/${params.projectId}`, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            },
          });
          if (response) {
            return response.data;
          } else {
            return null;
          }
        },
      },
      {
        path: '/projects/:projectId/datasets/:datasetId',
        element: <FlightForm />,
      },
    ],
  },
]);
