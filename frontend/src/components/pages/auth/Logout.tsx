import { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router';

import AuthContext from '../../../AuthContext';

export default function Logout() {
  const { logout } = useContext(AuthContext);
  const navigate = useNavigate();
  useEffect(() => {
    async function removeUserData() {
      localStorage.removeItem('projects');
      localStorage.removeItem('userProfile');
      await logout().then(() => navigate('/'));
    }
    removeUserData();
  }, []);
  return null;
}
