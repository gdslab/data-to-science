import { RouterProvider } from 'react-router-dom';
import './styles/custom.css';

import { AuthContextProvider } from './AuthContext';
import { router } from './router';

export default function App() {
  return (
    <AuthContextProvider>
      <RouterProvider router={router} />
    </AuthContextProvider>
  );
}
