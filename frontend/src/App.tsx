import { RouterProvider } from 'react-router-dom';
import './styles/custom.css';

import { router } from './router';

import { AuthContextProvider } from './AuthContext';

export default function App() {
  return (
    <AuthContextProvider>
      <RouterProvider router={router} />
    </AuthContextProvider>
  );
}
