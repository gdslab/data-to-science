import { RouterProvider } from 'react-router-dom';
import './styles/custom.css';

import { router } from './router';

import { AuthContextProvider } from './AuthContext';

export default function App() {
  return (
    <AuthContextProvider>
      <RouterProvider future={{ v7_startTransition: true }} router={router} />
    </AuthContextProvider>
  );
}
