import { Routes, Route } from 'react-router-dom';
import './styles/custom.css';

// pages
import ErrorPage from './components/ErrorPage';
import FlightForm from './components/forms/FlightForm';
import Landing from './components/Landing';
import LoginForm from './components/auth/LoginForm';
import Logout from './components/auth/Logout';
import Map from './components/map';
import Profile from './components/auth/Profile';
import ProjectDetail from './components/forms/ProjectDetail';
import ProjectForm from './components/forms/ProjectForm';
import ProjectList from './components/forms/ProjectList';
import RegistrationForm from './components/auth/RegistrationForm';
import { RootNonUser, RootUser } from './components/layout/Root';
import Teams from './components/forms/Teams/Teams';
import TeamDetail from './components/forms/TeamDetail';
import TeamForm from './components/forms/TeamForm';

// data loaders
import { loader as projectDetailLoader } from './components/forms/ProjectDetail/ProjectDetail';
import { loader as projectFormLoader } from './components/forms/ProjectForm/ProjectForm';
import { loader as projectListLoader } from './components/forms/ProjectList/ProjectList';
import { loader as teamDetailLoader } from './components/forms/TeamDetail/TeamDetail';
import { loader as teamsLoader } from './components/forms/Teams/Teams';

import { AuthContextProvider, RequireAuth } from './AuthContext';

export default function App() {
  return (
    <AuthContextProvider>
      <Routes>
        <Route element={<RootNonUser />} errorElement={<ErrorPage />}>
          <Route path="/" element={<Landing />} />
          <Route path="/auth/login" element={<LoginForm />} />
          <Route path="/auth/register" element={<RegistrationForm />} />
          <Route path="/auth/logout" element={<Logout />} />
        </Route>
        <Route
          element={
            <RequireAuth>
              <RootUser />
            </RequireAuth>
          }
          errorElement={<ErrorPage />}
        >
          <Route path="/home" element={<Map />} />
          <Route path="/auth/profile" element={<Profile />} />
          <Route path="/teams" element={<Teams />} loader={teamsLoader} />
          <Route
            path="/teams/:teamId"
            element={<TeamDetail />}
            loader={teamDetailLoader}
          />
          <Route path="/teams/create" element={<TeamForm />} />
          <Route
            path="/projects"
            element={<ProjectList />}
            loader={projectListLoader}
          />
          <Route
            path="/projects/create"
            element={<ProjectForm />}
            loader={projectFormLoader}
          />
          <Route
            path="/projects/:projectId"
            element={<ProjectDetail />}
            loader={projectDetailLoader}
          />
          <Route
            path="/projects/:projectId/datasets/:datasetId"
            element={<FlightForm />}
          />
        </Route>
      </Routes>
    </AuthContextProvider>
  );
}
