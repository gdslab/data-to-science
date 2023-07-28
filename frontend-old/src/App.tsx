import { RouterProvider } from "react-router-dom";

import { AuthContextProvider } from "./AuthContext";
import { router } from "./router";

export default function App() {
  return (
    <AuthContextProvider>
      <RouterProvider router={router} />
    </AuthContextProvider>
  );
}
