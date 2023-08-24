import { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import AuthContext from '../../../AuthContext';

export default function Logout() {
  const { logout } = useContext(AuthContext);
  const navigate = useNavigate();
  useEffect(() => {
    async function removeUserData() {
      localStorage.removeItem('userProfile');
      await logout().then(() => navigate('/'));
    }
    removeUserData();
  }, []);
  return null;
}
