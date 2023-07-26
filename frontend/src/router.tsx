import axios from "axios";
import { createBrowserRouter } from "react-router-dom";

import ErrorPage from "./components/ErrorPage";
import FlightForm from "./components/forms/FlightForm";
import LoginForm from "./components/forms/LoginForm";
import ProjectDetail from "./components/forms/ProjectDetail";
import ProjectForm from "./components/forms/ProjectForm";
import ProjectList from "./components/forms/ProjectList";
import RegistrationForm from "./components/forms/RegistrationForm";
import Root from "./components/layout/root";
import TeamForm from "./components/forms/TeamForm";
import TeamList from "./components/forms/TeamList";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Root />,
    errorElement: <ErrorPage />,
    children: [
      {
        path: "/register",
        element: <RegistrationForm />,
      },
      {
        path: "/login",
        element: <LoginForm />,
      },
      {
        path: "/teams",
        element: <TeamList />,
        loader: async () => {
          const response = await axios.get("/api/v1/teams/", {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("access_token")}`,
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
        path: "/teams/create",
        element: <TeamForm />,
      },
      {
        path: "/projects",
        element: <ProjectList />,
        loader: async () => {
          const response = await axios.get("/api/v1/projects/", {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("access_token")}`,
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
        path: "/projects/create",
        element: <ProjectForm />,
        loader: async () => {
          const response = await axios.get("/api/v1/teams/", {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            },
          });
          if (response) {
            const teams = response.data;
            teams.unshift({ title: "No team", id: "" });
            return teams;
          } else {
            return [];
          }
        },
      },
      {
        path: "/projects/:projectId",
        element: <ProjectDetail />,
        loader: async ({ params }) => {
          const response = await axios.get(`/api/v1/projects/${params.projectId}`, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("access_token")}`,
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
        path: "/projects/:projectId/datasets/:datasetId",
        element: <FlightForm />,
      },
    ],
  },
]);
