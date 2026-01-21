import { createBrowserRouter } from 'react-router';

// pages and data loaders
import Dashboard from './components/pages/admin/Dashboard';
import DashboardCharts, {
  loader as dashboardChartsLoader,
} from './components/pages/admin/DashboardCharts';
import DashboardExtensions, {
  loader as dashboardExtensionsLoader,
} from './components/pages/admin/DashboardExtensions';
import DashboardMap from './components/pages/admin/DashboardMap';
import DashboardProjectStorage, {
  loader as dashboardProjectStorageLoader,
} from './components/pages/admin/DashboardProjectStorage';
import DashboardSiteStatistics, {
  loader as dashboardSiteStatisticsLoader,
} from './components/pages/admin/DashboardSiteStatistics';
import DashboardUsers, {
  loader as dashboardUsersLoader,
} from './components/pages/admin/DashboardUsers';
import ErrorPage from './components/ErrorPage';
import FieldCampaignCreate from './components/pages/workspace/projects/fieldCampaigns/FieldCampaignCreate';
import FieldCampaignForm, {
  loader as fieldCampaignLoader,
} from './components/pages/workspace/projects/fieldCampaigns/FieldCampaignForm';
import FlightData, {
  loader as flightDataLoader,
} from './components/pages/workspace/projects/flights/FlightData';
import FlightForm, {
  loader as flightFormLoader,
} from './components/pages/workspace/projects/flights/FlightForm';
import IndoorProjectDetail, {
  loader as indoorProjectDetailLoader,
} from './components/pages/workspace/indoorProjects/IndoorProjectDetail';
import IndoorProjectPlantDetail, {
  loader as indoorProjectPlantDetailLoader,
} from './components/pages/workspace/indoorProjects/IndoorProjectPlantDetail';
import IndoorProjectAccess from './components/pages/workspace/indoorProjects/IndoorProjectAccess';
import IndoorProjectLayout from './components/pages/workspace/indoorProjects/IndoorProjectLayout';
import IForesterLayout from './components/pages/workspace/projects/iForester/IForesterLayout';
import Landing from './components/Landing';
import LoginForm from './components/pages/auth/LoginForm';
import Logout from './components/pages/auth/Logout';
import MapLayout from './components/maps/MapLayout';
import ShareMap from './components/maps/ShareMap';
import PasswordRecovery from './components/pages/auth/PasswordRecovery';
import PasswordResetForm from './components/pages/auth/PasswordResetForm';
import Profile from './components/pages/auth/Profile';
import ProjectAccess from './components/pages/workspace/projects/ProjectAccess';
import ProjectDetail from './components/pages/workspace/projects/ProjectDetail';
import ProjectLayout, {
  ProjectOutlet,
  loader as projectLayoutLoader,
} from './components/pages/workspace/projects/ProjectLayout';
import ProjectModules from './components/pages/workspace/projects/ProjectModules';
import ProjectSTACPublishing, {
  loader as stacPublishingLoader,
} from './components/pages/workspace/projects/stac/ProjectSTACPublishing';
import STACDisabled from './components/pages/workspace/projects/stac/STACDisabled';
import RegistrationForm from './components/pages/auth/RegistrationForm';
import { RasterSymbologyProvider } from './components/maps/RasterSymbologyContext';
import ShareLCCViewer from './components/maps/ShareLCCViewer';
import SharePanoViewer from './components/maps/SharePanoViewer';
import SharePlayCanvasglTFViewer from './components/maps/SharePlayCanvasglTFViewer';
import SharePotreeViewer from './components/maps/SharePotreeViewer';
import Teams, { loader as teamsLoader } from './components/pages/teams/Teams';
import TeamCreate, {
  loader as teamCreateLoader,
} from './components/pages/teams/TeamCreate';
import TeamDetail, {
  loader as teamDetailLoader,
} from './components/pages/teams/TeamDetail';
import Workspace, {
  loader as workspaceLoader,
} from './components/pages/Workspace';

import { RootPublic, RootProtected } from './components/layout/Root';
import { RequireAdmin, RequireAuth } from './AuthContext';

export const router = createBrowserRouter(
  [
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
          path: '/auth/recoverpassword',
          element: <PasswordRecovery />,
        },
        {
          path: '/auth/resetpassword',
          element: <PasswordResetForm />,
        },
        {
          path: '/sharemap',
          element: <RootProtected />,
          children: [
            {
              path: '/sharemap',
              element: (
                <RasterSymbologyProvider>
                  <ShareMap />
                </RasterSymbologyProvider>
              ),
            },
          ],
        },
        {
          path: '/share3dgs',
          element: <RootProtected />,
          children: [
            { path: '/share3dgs', element: <SharePlayCanvasglTFViewer /> },
          ],
        },
        {
          path: '/sharepano',
          element: <RootProtected />,
          children: [{ path: '/sharepano', element: <SharePanoViewer /> }],
        },
        {
          path: '/sharepotree',
          element: <RootProtected />,
          children: [{ path: '/sharepotree', element: <SharePotreeViewer /> }],
        },
        {
          path: '/sharelcc',
          element: <RootProtected />,
          children: [{ path: '/sharelcc', element: <ShareLCCViewer /> }],
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
              loader: teamCreateLoader,
            },
          ],
        },
        {
          path: '/projects',
          element: <ProjectLayout />,
          children: [
            {
              path: '/projects',
              element: <Workspace />,
              loader: workspaceLoader,
            },
            {
              // Nested route group for project-specific routes with shared loader
              path: '/projects/:projectId',
              id: 'projectLayout',
              element: <ProjectOutlet />,
              loader: projectLayoutLoader,
              children: [
                {
                  path: '/projects/:projectId/access',
                  element: <ProjectAccess />,
                },
                {
                  path: '/projects/:projectId/modules',
                  element: <ProjectModules />,
                },
                // Conditionally include STAC route based on environment variable
                ...(import.meta.env.VITE_STAC_ENABLED === 'true'
                  ? [
                      {
                        path: '/projects/:projectId/stac',
                        element: <ProjectSTACPublishing />,
                        loader: stacPublishingLoader,
                      },
                    ]
                  : [
                      {
                        path: '/projects/:projectId/stac',
                        element: <STACDisabled />,
                      },
                    ]),
                {
                  path: '/projects/:projectId/campaigns/create',
                  element: <FieldCampaignCreate />,
                },
                {
                  path: '/projects/:projectId/campaigns/:campaignId',
                  element: <FieldCampaignForm />,
                  loader: fieldCampaignLoader,
                },
                {
                  path: '/projects/:projectId/flights/:flightId/data',
                  element: <FlightData />,
                  loader: flightDataLoader,
                },
                {
                  path: '/projects/:projectId/flights/:flightId/edit',
                  element: <FlightForm editMode={true} />,
                  loader: flightFormLoader,
                },
                {
                  path: '/projects/:projectId/iforester',
                  element: <IForesterLayout />,
                },
                {
                  index: true,
                  element: <ProjectDetail />,
                },
              ],
            },
          ],
        },
        {
          path: '/indoor_projects',
          element: <IndoorProjectLayout />,
          children: [
            {
              path: '/indoor_projects',
              element: <Workspace />,
              loader: workspaceLoader,
            },
            {
              path: '/indoor_projects/:indoorProjectId',
              element: <IndoorProjectDetail />,
              loader: indoorProjectDetailLoader,
            },
            {
              path: '/indoor_projects/:indoorProjectId/access',
              element: <IndoorProjectAccess />,
            },
            {
              path: '/indoor_projects/:indoorProjectId/uploaded/:indoorProjectDataId/plants/:indoorProjectPlantId',
              element: <IndoorProjectPlantDetail />,
              loader: indoorProjectPlantDetailLoader,
            },
          ],
        },
      ],
    },
    {
      // admin pages
      element: (
        <RequireAdmin>
          <RootProtected />
        </RequireAdmin>
      ),
      errorElement: <ErrorPage />,
      children: [
        {
          path: '/admin/dashboard',
          element: <Dashboard />,
          children: [
            {
              path: '/admin/dashboard',
              element: <DashboardSiteStatistics />,
              loader: dashboardSiteStatisticsLoader,
            },
            {
              path: '/admin/dashboard/extensions',
              element: <DashboardExtensions />,
              loader: dashboardExtensionsLoader,
            },
            {
              path: '/admin/dashboard/map',
              element: <DashboardMap />,
            },
            {
              path: '/admin/dashboard/storage',
              element: <DashboardProjectStorage />,
              loader: dashboardProjectStorageLoader,
            },
            {
              path: '/admin/dashboard/users',
              element: <DashboardUsers />,
              loader: dashboardUsersLoader,
            },
            {
              path: '/admin/dashboard/charts',
              element: <DashboardCharts />,
              loader: dashboardChartsLoader,
            },
          ],
        },
      ],
    },
  ]
);
