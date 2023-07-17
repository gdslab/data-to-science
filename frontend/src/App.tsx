import { createBrowserRouter, RouterProvider } from "react-router-dom";

import ErrorPage from "./components/ErrorPage";
import FlightForm from "./components/forms/FlightForm";
import LoginForm from "./components/forms/LoginForm";
import ProjectForm from "./components/forms/ProjectForm";
import RegistrationForm from "./components/forms/RegistrationForm";
import Root from "./components/layout/root";

export default function App() {
  const router = createBrowserRouter([
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
          path: "/projects",
          element: <ProjectForm />,
        },
        {
          path: "/flights",
          element: <FlightForm />,
        },
      ],
    },
  ]);

  return (
    <>
      <RouterProvider router={router} />
    </>
  );
}
